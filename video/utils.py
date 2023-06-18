from yt_dlp import YoutubeDL
import whisper
import os
from mutagen.mp4 import MP4
from mutagen.mp3 import MP3
from .models import Video, Transcript
from core.models import Task
import openai
from moviepy.editor import VideoFileClip, AudioFileClip

# 定義與應用程式邏輯相關的工具函數（utils）


def process_video(task: Task):
    if task:
        # 如果有未處理的URL，進行處理
        trans_text = generate_transcript_from_file(task)
        store_transcript_info(task, trans_text)
        # 設置URL已處理
        task.status = "1"
        task.save()
        print("結束處理url")
    else:
        # 如果沒有未處理的URL，等待下一次啟動
        print("開始睡覺")


def process_synthesis(task: Task):
    # 讀取音頻檔案
    audioFilePath = (task.file.name).split("/")[-1].split(".")[0] + ".mp3"
    audioclip = AudioFileClip("downloads/" + audioFilePath)

    # 讀取視頻檔案
    videoclip = VideoFileClip(task.file.name)

    # 將音頻添加到視頻檔案，替換原本的音軌
    videoclip = videoclip.set_audio(audioclip)

    # 將結果輸出為一個新的視頻檔案
    output_path = (
        "downloads/video/" + (task.file.name).split("/")[-1].split(".")[0] + ".mp4"
    )
    videoclip.write_videofile(output_path, codec="libx264")


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


def generate_transcript_from_file(task: Task):
    location = task.file.name
    openai.api_key = os.getenv("OPENAI_API_KEY")
    audio_file = open(location, "rb")
    transcript = openai.Audio.transcribe("whisper-1", audio_file)
    if location.split(".")[-1] in ["mp4", "m4a"]:
        length = get_video_len(location)
    elif location.split(".")[-1] in ["mp3", "wav"]:
        length = get_audio_len(location)
    print(transcript)
    print("----------文字稿已生成----------")
    store_video_info(task, location, length)
    return transcript["text"]


def get_video_len(file_name):
    video = MP4(file_name)
    length = video.info.length
    return length


def get_audio_len(file_name):
    audio = MP3(file_name)
    length = audio.info.length
    return length


def store_video_info(task: Task, file_location, video_length):
    print("開始儲存影片")
    task.refresh_from_db()
    if task.status == "-1":
        raise Exception("任務已被取消")
    Video.objects.create(
        taskID=task, file_location=file_location, length=video_length, status=True
    )


def store_transcript_info(task: Task, trans_text):
    print("開始儲存文字稿")
    task.refresh_from_db()
    if task.status == "-1":
        raise Exception("任務已被取消")
    Transcript.objects.create(taskID=task, transcript=trans_text)
