import requests
import json
import time
from core.models import Task, TaskStatus
from translator.models import Deepl
from video.models import Video
from .models import Play_ht
import os
from pydub import AudioSegment
from pydub.utils import mediainfo
from django.core.files.storage import default_storage
from core.decorators import check_task_status


@check_task_status(TaskStatus.VOICE_PROCESSING)
def process_audio(task: Task):
    text = Deepl.objects.get(taskID=task).translated_text
    voice = task.voice_selection.voice
    task_file_name = task.get_file_basename()
    text_chunks = split_text_into_chunks(text, chunk_size=2500)

    audio_file_paths = []
    for i, text_chunk in enumerate(text_chunks):
        dic = make_voice(text_chunk, voice, 100)
        url = dic["audioUrl"]
        # 下載音訊檔案並儲存到本地，然後將路徑添加到列表中
        audio_file_path = f"audio-temp/{task_file_name}_{i}.mp3"
        download_audio(url, audio_file_path)
        audio_file_paths.append(audio_file_path)
    return audio_file_paths


@check_task_status(TaskStatus.VOICE_MERGE_PROCESSING)
def merge_audio_and_video(task: Task, audio_file_paths: list[str]):
    task_file_name = task.get_file_basename()
    origin_length = Video.objects.get(taskID=task).length
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
    Play_ht.objects.create(
        taskID=task,
        changed_audio_url=combined_audio_new_path,
        length_ratio=length_ratio,
        status=True,
    )
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
    print(dic)
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


def split_text_into_chunks(text, chunk_size):
    # 將文本分成指定大小的塊
    chunks = []
    while text:
        chunks.append(text[:chunk_size])
        text = text[chunk_size:]
    return chunks


def get_audio_length(audio_path):
    info = mediainfo(audio_path)
    return float(info["duration"])


def speed_change(sound, speed=1.0):
    # Manually override the frame_rate. This tells the computer how many
    # samples to play per second
    sound_with_altered_frame_rate = sound._spawn(
        sound.raw_data, overrides={"frame_rate": int(sound.frame_rate * speed)}
    )

    # convert the sound with altered frame rate to a standard frame rate
    # so that regular playback programs will work right. They often only
    # know how to play audio at standard frame rate
    return sound_with_altered_frame_rate.set_frame_rate(sound.frame_rate)
