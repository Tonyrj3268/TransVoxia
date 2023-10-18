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
import asyncio
import aiohttp
from aiofiles import open as aio_open
import re


@check_task_status(TaskStatus.VOICE_PROCESSING)
async def process_audio(task: Task,voice_list:list[str]):
    text = task.deepl.translated_text  # JsonField
    task_file_name = task.get_file_basename()
    # text_chunks = split_text_into_chunks(text, chunk_size=2500)
    ssml_list = get_ssml(text)
    audio_file_paths = []
    async with aiohttp.ClientSession() as session:
        tasks = []
        for ssml,voice in zip(ssml_list,voice_list):
            task = asyncio.ensure_future(make_voice_async(session, ssml, voice))
            tasks.append(task)

        responses = await asyncio.gather(*tasks)

        download_tasks = []
        for i, dic in enumerate(responses):
            url = dic["audioUrl"]
            audio_file_path = f"audio-temp/{task_file_name}_{i}.mp3"
            download_task = asyncio.ensure_future(
                download_audio_async(session, url, audio_file_path)
            )
            download_tasks.append(download_task)
            audio_file_paths.append(audio_file_path)

        await asyncio.gather(*download_tasks)
    return audio_file_paths

    # for i, text_chunk in enumerate(text_chunks):
    #     dic = make_voice(text_chunk, voice, 100)
    #     url = dic["audioUrl"]
    #     # 下載音訊檔案並儲存到本地，然後將路徑添加到列表中
    #     audio_file_path = f"audio-temp/{task_file_name}_{i}.mp3"
    #     download_audio(url, audio_file_path)
    #     audio_file_paths.append(audio_file_path)
    # return audio_file_paths


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


def split_text_into_chunks(text, chunk_size):
    chunks = []
    while text:
        chunks.append(text[:chunk_size])
        text = text[chunk_size:]
    return chunks


def get_audio_length(audio_path):
    info = mediainfo(audio_path)
    return float(info["duration"])


def speed_change(sound, speed=1.0):
    sound_with_altered_frame_rate = sound._spawn(
        sound.raw_data, overrides={"frame_rate": int(sound.frame_rate * speed)}
    )
    return sound_with_altered_frame_rate.set_frame_rate(sound.frame_rate)


async def make_voice_async(session, text, voice, speed=100):
    pattern = re.compile(r"(<speak>.*?</speak>)", re.DOTALL)
    speaks = pattern.findall(text)
    ssml = [speak.replace("\n", "").strip() for speak in speaks]

    payload = {
        "voice": voice,
        "content": ssml,
        "title": "Testing public api conversion",
        "globalSpeed": f"{speed}%",
    }
    headers = json.loads(os.getenv("PLAY_HT_API_KEY"))
    async with session.post(
        "https://play.ht/api/v1/convert", json=payload, headers=headers
    ) as response:
        json_response = await response.json()
        id = json_response["transcriptionId"]
        url = f"https://play.ht/api/v1/articleStatus?transcriptionId={id}"
    i = 0
    while True:
        async with session.get(url, headers=headers) as response:
            json_response = await response.json()
            message = json_response.get("message", "")

        if message == "Transcription still in progress":
            print("請稍等")
            i += 1
            if i > 12:
                print("請求超時")
                break
            await asyncio.sleep(10)  # 非同步等待
        else:
            return json_response


async def download_audio_async(session, url, path):
    async with session.get(url) as response:
        with await aio_open(path, "wb") as f:
            while chunk := await response.content.read(8192):
                await f.write(chunk)


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
