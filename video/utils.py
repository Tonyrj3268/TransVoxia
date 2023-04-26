from yt_dlp import YoutubeDL
import whisper
import os
from mutagen.mp4 import MP4
def download_youtube(url):
    ydl_opts = {}
    ydl_opts["format"] = "m4a"
    ydl_opts["outtmpl"] = "video-temp/"+"%(id)s.%(ext)s"

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def generate_transcript_from_url(url):
    location = "../tem-video/"+url.split("watch?v=")[1].split("&")[0]+".m4a"
    if not os.path.isfile(location):
        download_youtube(url)
    model = whisper.load_model("small")
    result_m4a = model.transcribe(location)
    origin = result_m4a["text"]
    length = get_audio_len(location)
    return origin, length

def get_audio_len(file_name):
    audio = MP4(file_name)
    length = audio.info.length
    print("Total length:", length)
    return length