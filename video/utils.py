import os
import traceback
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
    try:
        trans_text = generate_transcript_from_file(task)
        trans = Transcript.objects.create(transcript=trans_text)
        task.transcript = trans
        task.save()
    except Exception as e:
        error_message = "Failed to process transcript.\n" + traceback.format_exc()
        raise Exception(error_message) from e


@check_task_status(TaskStatus.VIDEO_MERGE_PROCESSING)
def process_synthesis(task: Task):
    try:
        audioFilePath = f"{task.get_file_basename()}.mp3"
        audioclip = AudioFileClip(f"translated/audio/{audioFilePath}")
        videoclip = VideoFileClip(task.fileLocation)
        newVideoclip = videoclip.set_audio(audioclip)
        output_path = f"translated/video/{task.get_file_basename()}.mp4"
        newVideoclip.write_videofile(output_path, codec="libx264")
        with open(output_path, "rb") as output_file:
            default_storage.save(output_path, output_file)
        audioclip.close()
        videoclip.close()
        newVideoclip.close()
    except Exception as e:
        error_message = "Failed to process synthesis.\n" + traceback.format_exc()
        raise Exception(error_message) from e


def generate_transcript_from_file(task: Task):
    location = task.fileLocation
    openai_api_key = os.getenv("OPENAI_API_KEY", None)
    if openai_api_key is None:
        raise Exception("OPENAI_API_KEY is not set in the environment variables.")
    openai.api_key = openai_api_key
    try:
        with open(location, "rb") as audio_file:
            transcript = openai.Audio.transcribe(
                file=audio_file, model="whisper-1", prompt=""
            )
    except Exception as e:
        error_message = "Failed to transcribe audio file.\n" + traceback.format_exc()
        raise Exception(error_message) from e
    extension = location.split(".")[-1]
    if extension in ["mp4", "m4a"]:
        length = MP4(location).info.length
    elif extension in ["mp3", "wav"]:
        length = MP3(location).info.length
    else:
        raise Exception(f"不支援的檔案格式：{extension}，路徑：{location}")
    video = Video.objects.create(file_location=location, length=length, status=True)
    task.video = video
    task.save()
    return transcript["text"]
