import os
import errno
from mutagen.mp4 import MP4
from mutagen.mp3 import MP3
from .models import Video, Transcript
from core.models import Task
import openai
from moviepy.editor import VideoFileClip, AudioFileClip
from django.core.files.storage import default_storage

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
    print("開始處理合成")
    # 讀取音頻檔案
    audioFilePath = (task.fileLocation).split("/")[-1].split(".")[0] + ".mp3"
    audioclip = AudioFileClip("translated/audio/" + audioFilePath)

    # 讀取視頻檔案
    videoclip = VideoFileClip(task.fileLocation)

    # 將音頻添加到視頻檔案，替換原本的音軌
    newVideoclip = videoclip.set_audio(audioclip)

    # 將結果輸出為一個新的視頻檔案
    output_path = (
        "translated/video/" + (task.fileLocation).split("/")[-1].split(".")[0] + ".mp4"
    )
    newVideoclip.write_videofile(output_path, codec="libx264")
    with open(output_path, "rb") as output_file:
        default_storage.save(output_path, output_file)
    audioclip.close()
    videoclip.close()
    newVideoclip.close()


def generate_transcript_from_file(task: Task):
    location = task.fileLocation
    openai.api_key = os.getenv("OPENAI_API_KEY")
    with open(location, "rb") as audio_file:
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
    if location.split(".")[-1] in ["mp4", "m4a"]:
        length = MP4(location).info.length
    elif location.split(".")[-1] in ["mp3", "wav"]:
        length = MP3(location).info.length
    print(transcript)
    print("----------文字稿已生成----------")
    store_video_info(task, location, length)
    return transcript["text"]


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
