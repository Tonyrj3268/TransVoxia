from yt_dlp import YoutubeDL
import whisper
import os
from mutagen.mp4 import MP4
from .models import Video, Transcript
from core.models import Task
import openai

# 定義與應用程式邏輯相關的工具函數（utils）


def process_video(task: Task):
    if task:
        # 如果有未處理的URL，進行處理
        trans_text = generate_transcript_from_chatgpt(task)
        store_transcript_info(task, trans_text)
        # 設置URL已處理
        task.status = "1"
        task.save()
        print("結束處理url")
    else:
        # 如果沒有未處理的URL，等待下一次啟動
        print("開始睡覺")


def download_youtube(url):
    ydl_opts = {}
    ydl_opts["format"] = "m4a"
    ydl_opts["outtmpl"] = "video-temp/" + "%(id)s.%(ext)s"

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


def generate_transcript_from_url(task: Task):
    url = task.url
    location = "video-temp/" + url.split("watch?v=")[1].split("&")[0] + ".m4a"
    if not os.path.isfile(location):
        download_youtube(url)
    model = whisper.load_model("small")
    result_m4a = model.transcribe(location)
    trans_text = result_m4a["text"]
    length = get_audio_len(location)
    store_video_info(task, location, length)
    return trans_text


def generate_transcript_from_chatgpt(task: Task):
    url = task.url
    location = "video-temp/" + url.split("watch?v=")[1].split("&")[0] + ".m4a"
    if not os.path.isfile(location):
        download_youtube(url)
    openai.api_key = os.getenv("OPENAI_API_KEY")
    audio_file = open(location, "rb")
    transcript = openai.Audio.transcribe("whisper-1", audio_file)
    length = get_audio_len(location)
    print(transcript)
    print("----------文字稿已生成----------")
    store_video_info(task, location, length)
    return transcript["text"]


def get_audio_len(file_name):
    audio = MP4(file_name)
    length = audio.info.length
    return length


def store_video_info(task: Task, file_location, video_length):
    print("開始儲存影片")
    Video.objects.create(
        taskID=task, file_location=file_location, length=video_length, status=True
    )


def store_transcript_info(task: Task, trans_text):
    print("開始儲存文字稿")
    transcript = Transcript.objects.create(taskID=task, transcript=trans_text)
