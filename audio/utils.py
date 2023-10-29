import asyncio
import csv
import json
import os
import re
from collections import OrderedDict, deque

import aiohttp
import auditok
import demucs.separate
import pandas as pd

from moviepy.editor import (
    AudioFileClip,
    CompositeAudioClip,
    concatenate_audioclips,
    VideoFileClip,
    concatenate_videoclips,
)

from core.decorators import check_task_status
from core.models import Task, TaskStatus

from .models import Play_ht
import torch


@check_task_status(TaskStatus.VOICE_PROCESSING)
async def process_audio(task: Task, voice_list: list[str]):
    text = await task.get_translated_text()
    task_file_name = task.get_file_basename()
    ssml_list = get_ssml(text)
    audio_file_paths = []

    async def handle_task(ssml, voice, audio_file_path):
        try:
            data = await make_voice(ssml, voice)
            url = data["audioUrl"]
            await download_audio(url, audio_file_path)
        except Exception as exc:
            print(f"Generated an exception: {exc}")

    tasks = []
    for ssml, voice in zip(ssml_list, voice_list):
        audio_file_path = f"audio-temp/{task_file_name}_{voice}.mp3"
        audio_file_paths.append(audio_file_path)
        task = handle_task(ssml, voice, audio_file_path)
        tasks.append(task)

    await asyncio.gather(*tasks)

    return audio_file_paths


@check_task_status(TaskStatus.VOICE_MERGE_PROCESSING)
def merge_audio(task: Task, audio_file_paths: list[str], csv_list: list[str]) -> str:
    task_file_name = task.get_file_basename()

    combined_audio_path = f"translated/audio/{task_file_name}.mp3"
    origin_file_path = task.fileLocation
    merge_vocal(task, csv_list, audio_file_paths, combined_audio_path, origin_file_path)
    playht = Play_ht.objects.create(
        changed_audio_url=combined_audio_path,
        status=True,
    )
    task.playht = playht
    task.save()

    return combined_audio_path


@check_task_status(TaskStatus.VOCAL_MERGE_BGMUSIC)
def merge_bgmusic_with_audio(task: Task, vocal_path: str, bg_music_path: str) -> str:
    # 讀取你的人聲檔
    # 讀取你的背景音樂檔
    with AudioFileClip(vocal_path) as vocal, AudioFileClip(
        bg_music_path
    ) as background_music:
        vocal_duration = vocal.duration
        bg_music_duration = background_music.duration
        # 如果背景音樂的持續時間小於視頻的持續時間，則更改背景音樂的速度以匹配視頻的持續時間
        if bg_music_duration < vocal_duration:
            speed_factor = vocal_duration / bg_music_duration
            background_music = background_music.fl_time(
                lambda t: t / speed_factor, apply_to=["audio"]
            )
            background_music = background_music.set_duration(vocal_duration)
        else:
            min_duration = min(vocal_duration, bg_music_duration)
            vocal = vocal.subclip(0, min_duration)
            background_music = background_music.subclip(0, min_duration)

        # 創建一個CompositeAudioClip對象並將兩個音頻剪輯合成為一個
        combined_audio = CompositeAudioClip(
            [vocal.volumex(0.8), background_music.volumex(0.2)]
        )
        # 將合成的音頻剪輯寫入新文件
        combined_audio.fps = 44100
        combined_audio.write_audiofile(vocal_path)
        combined_audio.close()
    return vocal_path


@check_task_status(TaskStatus.VOCAL_MERGE_BGMUSIC)
def merge_bgmusic_with_video(task: Task, video_path: str, bg_music_path: str) -> str:
    try:
        # 讀取你的人聲檔
        # 讀取你的背景音樂檔
        video = VideoFileClip(video_path)
        vocal = video.audio

        background_music = AudioFileClip(bg_music_path)
        video_duration = video.duration
        bg_music_duration = background_music.duration

        # 如果背景音樂的持續時間小於視頻的持續時間，則更改背景音樂的速度以匹配視頻的持續時間
        if bg_music_duration < video_duration:
            speed_factor = video_duration / bg_music_duration
            background_music = background_music.fl_time(
                lambda t: t / speed_factor, apply_to=["audio"]
            )
            background_music = background_music.set_duration(video_duration)
        else:
            min_duration = min(vocal.duration, bg_music_duration)
            vocal = vocal.subclip(0, min_duration)
            background_music = background_music.subclip(0, min_duration)

        # 創建一個CompositeAudioClip對象並將兩個音頻剪輯合成為一個
        combined_audio = CompositeAudioClip(
            [vocal.volumex(0.8), background_music.volumex(0.2)]
        )

        # 將合成的音頻剪輯寫入新文件
        video.audio = combined_audio
        video_path = video_path.replace(".mp4", "_bgmusic.mp4")
        video.write_videofile(video_path, audio_codec="aac", codec="h264_nvenc")
    except Exception as e:
        print(e)
    return video_path


@check_task_status(TaskStatus.VIDEO_MERGE_PROCESSING)
def merge_video(task: Task, audio_file_paths: list[str], csv_list: list[str]) -> str:
    origin_transcript = (
        task.transcript.modified_transcript
        if task.transcript.modified_transcript
        else task.transcript.transcript
    )
    video_path = task.fileLocation
    mp4 = VideoFileClip(video_path).without_audio()
    mp4_times = parse_timeline_file(origin_transcript)

    audio_clip_list = {}
    for input_mp3 in audio_file_paths:
        audio_clip_list[input_mp3] = AudioFileClip(input_mp3)
    mp3_trans_list = merge_csv(task, csv_list)
    ratios, _ = calculate_ratio_and_extremes(origin_transcript, mp3_trans_list)
    ratios.reset_index(drop=True, inplace=True)

    mp4_clips = []
    i = 0
    while i < len(mp4_times):
        _, mp4_start, mp4_end, mp4_content = mp4_times[i]
        speaker_mp3_path, mp3_start, mp3_end, _ = mp3_trans_list[i]
        mp4_duration = mp4_end - mp4_start
        if mp4_end > mp4.duration:
            mp4_end = mp4.duration - 0.01
        mp4_clip = mp4.subclip(mp4_start, mp4_end)
        if mp4_content and mp4_content != "---":
            mp3_clip = audio_clip_list[speaker_mp3_path].subclip(
                mp3_start, float(mp3_end) + 0.1
            )
            if ratios[i] > 1:
                mp4_clip = mp4_clip.speedx(1 / ratios[i])
            mp4_clip = mp4_clip.set_audio(mp3_clip)

        else:
            mp4_clip = mp4_clip.speedx(mp4_duration / (mp4_duration + 0.2))
        mp4_clips.append(mp4_clip)
        i += 1
    output_mp4 = f"translated/video/{task.get_file_basename()}.mp4"
    final_clip = concatenate_videoclips(mp4_clips)
    final_clip.write_videofile(output_mp4, audio_codec="aac", codec="h264_nvenc")

    mp4.close()
    for input_mp3 in audio_file_paths:
        audio_clip_list[input_mp3].close()

    return output_mp4


async def make_voice(text, voice, speed=100):
    pattern = re.compile(r"(<speak>.*?</speak>)", re.DOTALL)
    speaks = pattern.findall(text)
    ssml = [speak.strip() for speak in speaks]
    payload = json.dumps(
        {
            "voice": voice,
            "ssml": ssml,
            "title": "Testing public api convertion",
            "globalSpeed": str(speed) + "%",
        }
    )
    headers = {
        "accept": "application/json",
        "AUTHORIZATION": "6d1275331bc1403ebd28045f7b8d9f5e",
        "X-USER-ID": "9X30i7n3LMTk9OyzeTvSGxG9snO2",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://play.ht/api/v1/convert/", json=json.loads(payload), headers=headers
        ) as response:
            res_json = await response.json()
            id = res_json["transcriptionId"]
            url = "https://play.ht/api/v1/articleStatus?transcriptionId=" + id

    i = 0
    wait_time = 10
    while True:
        dic = await check_voice_make(url)
        if dic != True:
            break
        i += 1
        if i > 12:
            print("請求超時")
            break
        await asyncio.sleep(wait_time)
        wait_time = min(wait_time * 2, 60)

    return dic


async def check_voice_make(url):
    headers = json.loads(os.getenv("PLAY_HT_API_KEY"))

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            text = await response.text()
            dict_data = json.loads(
                text,
                object_pairs_hook=lambda x: {
                    k: True if v == "true" else False if v == "false" else v
                    for k, v in x
                },
            )

    if dict_data["message"] == "Transcription still in progress":
        print("請稍等")
        await asyncio.sleep(10)
        return True
    else:
        return dict_data


async def download_audio(url, path):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                response.raise_for_status()
            with open(path, "wb") as f:
                while True:
                    chunk = await response.content.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)


def get_ssml(transcipts_json):
    speaker_set = {}
    last_speaker = None
    if transcipts_json[0][0] == "Silence":
        speaker_set[transcipts_json[1][0]] = {"times": 0, "content": "<speak>"}
        last_speaker = transcipts_json[1][0]
        transcipts_json = transcipts_json[1:]
    for row in transcipts_json:
        speaker, start_time, end_time, text = row
        if speaker not in speaker_set and speaker != "Silence":
            speaker_set[speaker] = {"times": 0, "content": "<speak>"}
        # 检查这一行是否是 --- 行
        if speaker == "Silence":
            # 计算持续时间（秒）
            duration = float(end_time) - float(start_time)
            speaker_set[last_speaker][
                "content"
            ] += f"<break time='{round(duration+3,2)}s'/>"
        else:
            # 如果这一行不是 --- 行，那么就把它加到结果字符串中
            current_text = text.lstrip().replace(" ", "")
            if current_text[-1] not in ".?!。？！":
                current_text += "."
            speaker_set[speaker]["content"] += current_text
            last_speaker = speaker
            if (
                len(speaker_set[speaker]["content"])
                > (speaker_set[speaker]["times"] + 1) * 2000
            ):
                speaker_set[speaker]["content"] += "</speak>"
                speaker_set[speaker]["content"] += "<speak>"
                speaker_set[speaker]["times"] += 1
    ssml_list = []

    for speaker in speaker_set:
        speaker_set[speaker]["content"] += "</speak>"
        ssml_list.append(speaker_set[speaker]["content"])
    return ssml_list


def split_bg_music(origin_mp4, output_dir):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Split bgmusic using device {device}")
    demucs.separate.main(
        [
            "--device",
            device,
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
        with open(output_csv, "w", encoding="utf-8", newline="") as output_file:
            writer = csv.writer(output_file)
            for line in formatted_entries_rounded:
                writer.writerow(line)
    except Exception as e:
        print(e)


def calculate_ratio_and_extremes(origin_trans, new_trans):
    # 讀取文件
    new_df = pd.DataFrame(new_trans, columns=["Speaker", "Start", "End", "Content"])
    new_df = new_df.astype({"Start": float, "End": float})
    origin_df = pd.DataFrame(
        origin_trans, columns=["Speaker", "Start", "End", "Content"]
    )
    origin_df = origin_df.astype({"Start": float, "End": float})
    # 過濾包含 '---' 的行
    new_filtered = new_df[new_df.iloc[:, 2] != "---"].copy()
    origin_filtered = origin_df[origin_df.iloc[:, 2] != "---"].copy()

    # 計算每一行的時間軸長度
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
def parse_timeline_file(trans: list) -> list:
    times = []

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


def merge_csv(task: Task, csv_paths: list[str]):
    # original_rows = task.transcript.modified_transcript if task.transcript.modified_transcript else task.transcript.transcript
    original_rows = task.transcript.transcript
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
    for i, row in enumerate(original_rows):
        speaker, _, _, content = row
        new_speaker = speaker_to_filename.get(speaker, speaker)  # 使用CSV檔名作為新的speaker
        if new_speaker != "Silence":
            base_name = new_speaker.split(".")[0]
            new_speaker = os.path.join(base_name + ".mp3")
        new_start_time, new_end_time = None, None
        if (speaker in time_update_queues) and time_update_queues[speaker]:
            new_start_time, new_end_time = time_update_queues[speaker].popleft()
        new_start_time = new_start_time if new_start_time is not None else row[1]
        new_end_time = new_end_time if new_end_time is not None else row[2]
        new_rows.append([new_speaker, new_start_time, new_end_time, content])
    return new_rows


def merge_vocal(task: Task, csv_paths, input_mp3_list, output_mp3, origin_file_path):
    origin_transcript = (
        task.transcript.modified_transcript
        if task.transcript.modified_transcript
        else task.transcript.transcript
    )

    origin = AudioFileClip(origin_file_path).fx(lambda audio: audio.volumex(0))

    mp4_times = parse_timeline_file(origin_transcript)
    audio_clip_list = {}
    for input_mp3 in input_mp3_list:
        audio_clip_list[input_mp3] = AudioFileClip(input_mp3)

    mp3_trans_list = merge_csv(task, csv_paths)

    ratios, _ = calculate_ratio_and_extremes(origin_transcript, mp3_trans_list)
    ratios.reset_index(drop=True, inplace=True)
    # 存儲剪切的片段
    mp3_clips = []
    i = 0
    while i < len(mp4_times):
        _, mp4_start, mp4_end, mp4_content = mp4_times[i]
        speaker_mp3_path, mp3_start, mp3_end, _ = mp3_trans_list[i]

        mp4_duration = mp4_end - mp4_start

        origin_clip = origin.subclip(mp4_start, mp4_end)

        if mp4_content and mp4_content != "---":
            mp3_clip = audio_clip_list[speaker_mp3_path].subclip(
                mp3_start, float(mp3_end) + 0.1
            )
            mp3_clips.append(mp3_clip)
        else:
            origin_clip = origin_clip.audio_loop(duration=mp4_duration + 0.2)
            mp3_clips.append(origin_clip)
        i += 1

    final_clip = concatenate_audioclips(mp3_clips)
    final_clip.write_audiofile(output_mp3)
    origin.close()
    for input_mp3 in input_mp3_list:
        audio_clip_list[input_mp3].close()
