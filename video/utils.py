import os
from mutagen.mp4 import MP4
from mutagen.mp3 import MP3
from .models import Video, Transcript
from core.models import Task, TaskStatus
from core.decorators import check_task_status
import openai
from moviepy.editor import VideoFileClip, AudioFileClip
from django.core.files.storage import default_storage


@check_task_status(TaskStatus.TRANSCRIPT_PROCESSING)
def process_transcript(task: Task):
    trans_text = generate_transcript_from_file(task)
    Transcript.objects.create(taskID=task, transcript=trans_text)


@check_task_status(TaskStatus.VIDEO_MERGE_PROCESSING)
def process_synthesis(task: Task):
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
        transcript = openai.Audio.transcribe(
            file=audio_file, model="whisper-1", prompt=""
        )
    if location.split(".")[-1] in ["mp4", "m4a"]:
        length = MP4(location).info.length
    elif location.split(".")[-1] in ["mp3", "wav"]:
        length = MP3(location).info.length
    Video.objects.create(
        taskID=task, file_location=location, length=length, status=True
    )
    return transcript["text"]
