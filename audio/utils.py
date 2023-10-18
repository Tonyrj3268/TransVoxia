import requests
import json
import time
from core.models import Task, TaskStatus
from .models import Play_ht
import os
from pydub import AudioSegment
from pydub.utils import mediainfo
from django.core.files.storage import default_storage
from core.decorators import check_task_status
from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    concatenate_videoclips,
)
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
import auditok
import csv
import demucs.separate
import pandas as pd
@check_task_status(TaskStatus.VOICE_PROCESSING)
def process_audio(task: Task,voice_list:list[str]):
    text = task.deepl.translated_text  # JsonField
    task_file_name = task.get_file_basename()
    ssml_list = get_ssml(text)
    audio_file_paths = []
    with ThreadPoolExecutor() as executor:
        future_to_task = {}
        for ssml, voice in zip(ssml_list, voice_list):
            future = executor.submit(make_voice, ssml, voice)
            future_to_task[future] = (ssml, voice)
        for future in concurrent.futures.as_completed(future_to_task):
            ssml, voice = future_to_task[future]
            try:
                data = future.result()
                url = data["audioUrl"]
                audio_file_path = f"audio-temp/{task_file_name}_{voice}.mp3"
                executor.submit(download_audio, url, audio_file_path)
                audio_file_paths.append(audio_file_path)
            except Exception as exc:
                print(f'Generated an exception: {exc}')
    return audio_file_paths


@check_task_status(TaskStatus.VOICE_MERGE_PROCESSING)
def merge_audio_and_video(task: Task, audio_file_paths: list[str]):
    task_file_name = task.get_file_basename()
    origin_length = task.video.length
    combined_audio_path = f"audio-temp/{task_file_name}_complete.mp3"
    combine_audio_files(audio_file_paths, combined_audio_path)

    length_ratio = round(
        get_audio_length(combined_audio_path) / float(origin_length), 3
    )

    fast_sound = speed_change(
        AudioSegment.from_file(combined_audio_path, format="mp3"), length_ratio
    )
    for path in audio_file_paths:
        os.remove(path)
    os.remove(combined_audio_path)
    combined_audio_new_path = f"translated/audio/{task_file_name}.mp3"
    fast_sound.export(combined_audio_new_path, format="mp3")
    playht = Play_ht.objects.create(
        changed_audio_url=combined_audio_new_path,
        length_ratio=length_ratio,
        status=True,
    )
    task.playht = playht
    task.save()
    with open(combined_audio_new_path, "rb") as output_file:
        default_storage.save(combined_audio_new_path, output_file)

@check_task_status(TaskStatus.VOICE_MERGE_PROCESSING)
def merge_audio_and_bgmusic(task: Task, audio_file_paths: list[str],csv_list,bgmusic_path:str=None):
    task_file_name = task.get_file_basename()

    combined_audio_path = f"audio-temp/{task_file_name}_complete.mp3"
    merge_vocal(task,csv_list,audio_file_paths,task.transcript.transcript,combined_audio_path)

    for path in audio_file_paths:
        os.remove(path)
    os.remove(combined_audio_path)
    combined_audio_new_path = f"translated/audio/{task_file_name}.mp3"
    playht = Play_ht.objects.create(
        changed_audio_url=combined_audio_new_path,
        status=True,
    )
    task.playht = playht
    task.save()
    with open(combined_audio_new_path, "rb") as output_file:
        default_storage.save(combined_audio_new_path, output_file)

def make_voice(text, voice, speed=100):
    payload = json.dumps(
        {
            "voice": voice,
            "content": [text],
            "title": "Testing public api convertion",
            "globalSpeed": str(speed) + "%",
        }
    )
    headers = json.loads(os.getenv("PLAY_HT_API_KEY"))
    response = requests.request(
        "POST", "https://play.ht/api/v1/convert", headers=headers, data=payload
    )
    id = response.json()["transcriptionId"]
    url = "https://play.ht/api/v1/articleStatus?transcriptionId=" + id

    i = 0
    while (dic := check_voice_make(url)) == True:
        i += 1
        if i > 12:
            print("請求超時")
            break
    return dic


def check_voice_make(url):
    headers = json.loads(os.getenv("PLAY_HT_API_KEY"))
    response = requests.request("GET", url, headers=headers)
    dict_data = json.loads(
        response.text,
        object_pairs_hook=lambda x: {
            k: True if v == "true" else False if v == "false" else v for k, v in x
        },
    )
    if dict_data["message"] == "Transcription still in progress":
        print("請稍等")
        time.sleep(10)
        return True
    else:
        return dict_data


def download_audio(url, path):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)


def combine_audio_files(audio_file_paths, output_path):
    combined = AudioSegment.empty()

    for path in audio_file_paths:
        audio = AudioSegment.from_mp3(path)
        combined += audio

    combined.export(output_path, format="mp3")


def get_audio_length(audio_path):
    info = mediainfo(audio_path)
    return float(info["duration"])


def speed_change(sound, speed=1.0):
    sound_with_altered_frame_rate = sound._spawn(
        sound.raw_data, overrides={"frame_rate": int(sound.frame_rate * speed)}
    )
    return sound_with_altered_frame_rate.set_frame_rate(sound.frame_rate)


def get_ssml(transcipts_json):
    speaker_set = {}
    last_speaker = None
    if transcipts_json[0][0] == "Silence":
        speaker_set[transcipts_json[1][0]] = {"times": 0, "content": "<speak>\n"}
        last_speaker = transcipts_json[1][0]
        transcipts_json = transcipts_json[1:]
    for row in transcipts_json:
        speaker, start_time, end_time, text = row
        if speaker not in speaker_set and speaker != "Silence":
            speaker_set[speaker] = {"times": 0, "content": "<speak>\n"}
        # 检查这一行是否是 --- 行
        if speaker == "Silence":
            # 计算持续时间（秒）
            duration = float(end_time) - float(start_time)
            speaker_set[last_speaker][
                "content"
            ] += f"<break time='{round(duration+3,2)}s'/>\n"
        else:
            # 如果这一行不是 --- 行，那么就把它加到结果字符串中
            current_text = text.lstrip().replace(" ", "")
            if current_text[-1] not in ".?!。？！":
                current_text += "."
            speaker_set[speaker]["content"] += current_text
            speaker_set[speaker]["content"] += "\n"
            last_speaker = speaker
            if (
                len(speaker_set[speaker]["content"])
                > (speaker_set[speaker]["times"] + 1) * 2000
            ):
                speaker_set[speaker]["content"] += "</speak>\n"
                speaker_set[speaker]["content"] += "<speak>\n"
                speaker_set[speaker]["times"] += 1
    ssml_list = []
    for speaker in speaker_set:
        speaker_set[speaker]["content"] += "</speak>"
        ssml_list.append(speaker_set[speaker]["content"])

    return ssml_list


def split_bg_music(origin_mp4, output_dir):
    demucs.separate.main(
        [
            "--mp3",
            "--two-stems",
            "vocals",
            "-n",
            "mdx_extra",
            "-o",
            output_dir,
            origin_mp4,
        ]
    )

def auditok_detect(input_audio, output_csv):
    try:
        region = auditok.load(input_audio)
        audio_regions = list(
            region.split(
                max_dur=30,
                min_dur=0.3,
                max_silence=3,  # 設置為 2.5 秒以捕獲超過 3 秒的靜默區域
                energy_threshold=55,
            )
        )
        combined_entries = []
        for i, r in enumerate(audio_regions):
            # if i == 0 and need_split and r.meta.start > 0:
            #     combined_entries.append(
            #         {"start": 0, "end": round(r.meta.start, 2), "text": "---"}
            #     )
            begin = round(r.meta.start, 2)
            end = round(r.meta.end - 3, 2)
            if i == len(audio_regions) - 1:
                end = round(r.meta.end, 2)
            combined_entries.append({"start": begin, "end": end, "text": "xxx"})
            # if i != len(audio_regions) - 1 and end != audio_regions[i + 1].meta.start:
            #     combined_entries.append(
            #         {
            #             "start": end,
            #             "end": round(audio_regions[i + 1].meta.start, 2),
            #             "text": "---",
            #         }
            #     )

        formatted_entries_rounded = [
            (entry["start"], entry["end"], entry["text"].strip())
            for entry in combined_entries
        ]
        with open(
            output_csv,
            "w",
            encoding="utf-8",
            newline=''
        ) as output_file:
            writer = csv.writer(output_file)
            for line in formatted_entries_rounded:
                writer.writerow(line)
    except Exception as e:
        print(e)

def calculate_ratio_and_extremes(origin_file, new_file):
    # 讀取文件
    new_df = pd.DataFrame(new_file, columns=["Speaker", "Start", "End", "Content"])
    origin_df = pd.read_csv(origin_file, header=None)

    # 過濾包含 '---' 的行
    new_filtered = new_df[new_df.iloc[:, 2] != "---"].copy()
    origin_filtered = origin_df[origin_df.iloc[:, 2] != "---"].copy()

    # 計算每一行的時間軸長度
    new_filtered.iloc[:, 2] = new_filtered.iloc[:, 2].astype(float)
    new_filtered.iloc[:, 1] = new_filtered.iloc[:, 1].astype(float)
    new_filtered["length"] = new_filtered.iloc[:, 2] - new_filtered.iloc[:, 1]
    origin_filtered["length"] = origin_filtered.iloc[:, 2] - origin_filtered.iloc[:, 1]

    # 計算比值
    ratios = (new_filtered["length"]) / origin_filtered["length"]
    ratio = 1
    # 計算偏差值並去除
    if (ratios > 1).sum() > (ratios < 1).sum():
        ratios_filtered = ratios[ratios > 1]
        ratio = ratios_filtered.min()
    else:
        ratios_filtered = ratios[ratios < 1]
        ratio = ratios_filtered.max()
    time_diffs = (
        (new_filtered["length"] - origin_filtered["length"] * ratio).abs().tolist()
    )
    return ratios, time_diffs


# 讀取時間軸檔案並解析
def parse_timeline_file(task:Task) -> list:
    times = []
    trans=task.transcript.transcript
    if task.transcript.modified_transcript:
        trans = task.transcript.modified_transcript
    for row in trans:
        speaker, start_time, end_time, content = row
        times.append(
            (
                speaker,
                float(start_time.strip()),
                float(end_time.strip()),
                content.strip(),
            )
        )
    return times


from collections import deque, OrderedDict


def merge_csv(task:Task, csv_paths):
    original_rows = task.transcript.modified_transcript if task.transcript.modified_transcript else task.transcript.transcript
    speaker_set = OrderedDict(
        (row[0], None) for row in original_rows if row[0] != "Silence"
    )
    # 創建一個從原始speaker到CSV檔名的映射
    speaker_to_filename = {
        speaker: path for speaker, path in zip(speaker_set, csv_paths)
    }
    # 讀取csv_paths中的每個文件，並創建一個用於更新時間的隊列
    time_update_queues = {}
    for speaker, path in zip(speaker_set, csv_paths):
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            time_update_queues[speaker] = deque([(row[0], row[1]) for row in reader])
    new_rows = []
    for row in original_rows:
        speaker, _, _, content = row
        new_speaker = speaker_to_filename.get(speaker, speaker)  # 使用CSV檔名作為新的speaker
        if new_speaker != "Silence":
            base_name = new_speaker.split(".")[0]
            new_speaker = os.path.join(base_name + ".mp3")
        new_start_time, new_end_time = None, None

        if speaker in time_update_queues and time_update_queues[speaker]:
            new_start_time, new_end_time = time_update_queues[speaker].popleft()

        new_start_time = new_start_time if new_start_time is not None else row[1]
        new_end_time = new_end_time if new_end_time is not None else row[2]
        new_rows.append([new_speaker, new_start_time, new_end_time, content])
    return new_rows

def merge_video_vocal(
    input_mp4,
    input_mp3_list,
    input_mp4_transcript,
    input_mp3_transcript_list,
    output_mp4,
):
    mp4 = VideoFileClip(input_mp4).without_audio()
    mp4_times = parse_timeline_file(input_mp4_transcript)

    audio_clip_list = {}
    for input_mp3 in input_mp3_list:
        audio_clip_list[input_mp3] = AudioFileClip(input_mp3)
    mp3_trans_list = merge_csv(input_mp4_transcript, input_mp3_transcript_list)
    ratios, _ = calculate_ratio_and_extremes(input_mp4_transcript, mp3_trans_list)
    ratios.reset_index(drop=True, inplace=True)
    # 存儲剪切的片段
    mp4_clips = []
    i = 0
    while i < len(mp4_times):
        speaker_mp4, mp4_start, mp4_end, mp4_content = mp4_times[i]
        speaker_mp3_path, mp3_start, mp3_end, _ = mp3_trans_list[i]
        mp3_duration = float(mp3_end) - float(mp3_start)
        mp4_duration = mp4_end - mp4_start
        print(mp4_end, mp4.duration)
        if mp4_end > mp4.duration:
            print("mp4_end > mp4.duration")
            mp4_end = mp4.duration-0.01
        try:
            mp4_clip = mp4.subclip(mp4_start, mp4_end)
        except Exception as e:
            print(e)
        if mp4_content and mp4_content != "---":
            mp3_clip = audio_clip_list[speaker_mp3_path].subclip(
                mp3_start, float(mp3_end) + 0.1
            )
            # txt_clip = TextClip(mp4_content, fontsize=24, color="white",method="caption", align="South", stroke_color="black", stroke_width=1, font="Noto-Sans-TC-Bold")
            # txt_clip = txt_clip.set_duration(mp3_clip.duration)
            if ratios[i] > 1:
                mp4_clip = mp4_clip.speedx(1 / ratios[i])
            # mp4_clip = mp4_clip.speedx(1 / ratios[i])
            # mp4_clip = CompositeVideoClip([mp4_clip, txt_clip])
            mp4_clip = mp4_clip.set_audio(mp3_clip)

        else:
            mp4_clip = mp4_clip.speedx(mp4_duration / (mp4_duration + 0.2))
        mp4_clips.append(mp4_clip)
        i += 1

    final_clip = concatenate_videoclips(mp4_clips)
    final_clip.write_videofile(output_mp4)

def merge_vocal(
    task,
    csv_paths,
    input_mp3_list,
    input_mp4_transcript,
    output_mp4,
):
    mp4_times = parse_timeline_file(input_mp4_transcript)
    print(mp4_times)
    audio_clip_list = {}
    for input_mp3 in input_mp3_list:
        audio_clip_list[input_mp3] = AudioFileClip(input_mp3)
    mp3_trans_list = merge_csv(task, csv_paths)
    ratios, _ = calculate_ratio_and_extremes(input_mp4_transcript, mp3_trans_list)
    ratios.reset_index(drop=True, inplace=True)
    # 存儲剪切的片段
    mp4_clips = []
    i = 0
    while i < len(mp4_times):
        speaker_mp4, mp4_start, mp4_end, mp4_content = mp4_times[i]
        speaker_mp3_path, mp3_start, mp3_end, _ = mp3_trans_list[i]
        mp3_duration = float(mp3_end) - float(mp3_start)
        mp4_duration = mp4_end - mp4_start
        if mp4_content and mp4_content != "---":
            mp3_clip = audio_clip_list[speaker_mp3_path].subclip(
                mp3_start, float(mp3_end) + 0.1
            )
            # txt_clip = TextClip(mp4_content, fontsize=24, color="white",method="caption", align="South", stroke_color="black", stroke_width=1, font="Noto-Sans-TC-Bold")
            # txt_clip = txt_clip.set_duration(mp3_clip.duration)
            if ratios[i] > 1:
                mp4_clip = mp4_clip.speedx(1 / ratios[i])
            # mp4_clip = mp4_clip.speedx(1 / ratios[i])
            # mp4_clip = CompositeVideoClip([mp4_clip, txt_clip])
            mp4_clip = mp4_clip.set_audio(mp3_clip)

        else:
            mp4_clip = mp4_clip.speedx(mp4_duration / (mp4_duration + 0.2))
        mp4_clips.append(mp4_clip)
        i += 1

    final_clip = concatenate_videoclips(mp4_clips)
    final_clip.write_videofile(output_mp4)