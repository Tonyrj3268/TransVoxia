import traceback
from mutagen.mp4 import MP4
from mutagen.mp3 import MP3
from .models import Video, Transcript
from core.models import Task, TaskStatus
from core.decorators import check_task_status
from moviepy.editor import VideoFileClip, AudioFileClip
from django.core.files.storage import default_storage
import whisperx
import torch

@check_task_status(TaskStatus.TRANSCRIPT_PROCESSING)
def process_transcript(task: Task) -> None:
    try:
        trans_text = generate_transcript_from_file(task)
        trans = Transcript.objects.create(transcript=trans_text)
        task.transcript = trans
        task.save()
    except Exception as e:
        error_message = "Failed to process transcript.\n" + traceback.format_exc()
        raise Exception(error_message) from e


@check_task_status(TaskStatus.VIDEO_MERGE_PROCESSING)
def process_synthesis(task: Task) -> None:
    try:
        audioFilePath = f"{task.get_file_basename()}.mp3"
        with AudioFileClip(
            f"translated/audio/{audioFilePath}"
        ) as audioclip, VideoFileClip(task.fileLocation) as videoclip:
            newVideoclip = videoclip.set_audio(audioclip)
            output_path = f"translated/video/{task.get_file_basename()}.mp4"
            newVideoclip.write_videofile(
                output_path, codec="libx264", audio_codec="aac"
            )
        with open(output_path, "rb") as output_file:
            default_storage.save(output_path, output_file)
        newVideoclip.close()
    except Exception as e:
        error_message = "Failed to process synthesis.\n" + traceback.format_exc()
        raise Exception(error_message) from e


def generate_transcript_from_file(task: Task) -> str:
    location = task.fileLocation
    try:
        formatted_entries,speakers = get_entries(location)
    except Exception as e:
        error_message = "Failed to transcribe audio file.\n" + traceback.format_exc()
        raise Exception(error_message) from e
    extension = location.split(".")[-1]
    if extension in ["mp4", "m4a"]:
        length = MP4(location).info.length  # type: ignore
    elif extension in ["mp3", "wav"]:
        length = MP3(location).info.length  # type: ignore
    else:
        raise Exception(f"不支援的檔案格式：{extension}，路徑：{location}")
    video = Video.objects.create(file_location=location, length=length,speaker_counts=len(speakers), status=True)
    task.video = video
    task.save()
    return formatted_entries


def ends_with_punctuation(s):
    return s[-1] in ".!?。？！"


def format_time(time):
    """Format the time to have two decimal places."""
    return "{:.2f}".format(time)


def get_transcript(file_path: str) -> list:
    device = "cuda"
    batch_size = 16  # reduce if low on GPU mem
    compute_type = "float16"  # change to "int8" if low on GPU mem (may reduce accuracy)
    
    model = whisperx.load_model("large-v2", device, compute_type=compute_type)
    audio = whisperx.load_audio(file_path)
    result = model.transcribe(audio, batch_size=batch_size)
    model_a, metadata = whisperx.load_align_model(
        language_code=result["language"], device=device
    )
    
    result = whisperx.align(
        result["segments"],
        model_a,
        metadata,
        audio,
        device,
        return_char_alignments=False,
    )
    diarize_model = whisperx.DiarizationPipeline(
        use_auth_token="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", device=device
    )
    diarize_segments = diarize_model(audio)

    result = whisperx.assign_word_speakers(diarize_segments, result)
    return result["segments"]


def get_entries(file_path: str):
    entries = []
    speaker = set()
    time_stamp_transcript = get_transcript(file_path)
    for segment in time_stamp_transcript:
        for j,word in enumerate(segment["words"]):
            try:
                entries.append(
                    {
                        "speaker": word["speaker"],
                        "start": word["start"],
                        "end": word["end"],
                        "word": word["word"],
                    }
                )
                speaker.add(segment["speaker"])
                # if j == len(segment["words"])-1 and not ends_with_punctuation(word["word"]):
                #     entries[-1]["word"] += "."
            except Exception as e:
                print(e)
                pass

    combined_entries = []
    current_entry = None
    current_text = ""
    i = 0
    for entry in entries:
        i += 1
        if current_entry is None:
            current_entry = {
                "speaker": entry["speaker"],
                "start": entry["start"],
                "end": entry["end"],
                "text": entry["word"].strip(),
            }
            current_text = entry["word"].strip()
        else:
            current_text += " " + entry["word"].strip()
            current_entry["end"] = entry["end"]

        if ends_with_punctuation(current_text):
            current_entry["text"] = current_text
            combined_entries.append(current_entry)
            current_entry = None
            current_text = ""
    output_entries = []
    current_entry = None
    if combined_entries[0]["start"] > 0:
        output_entries.append(
            {
                "speaker": "Silence",
                "start": 0,
                "end": combined_entries[0]["start"],
                "text": "---",
            }
        )

    for idx, entry in enumerate(combined_entries):
        output_entries.append(entry)
        if idx + 1 < len(combined_entries):
            output_entries.append(
                {
                    "speaker": "Silence",
                    "start": entry["end"],
                    "end": combined_entries[idx + 1]["start"],
                    "text": "---",
                }
            )
    formatted_entries_rounded = [
        (
            entry["speaker"],
            format_time(entry["start"]),
            format_time(entry["end"]),
            entry["text"],
        )
        for entry in output_entries
    ]
    formatted_entries_rounded.append(
        (
            "Silence",
            formatted_entries_rounded[-1][2],
            str(float(formatted_entries_rounded[-1][2]) + 1),
            "---",
        )
    )
    file_path = r"C:\Users\soslab\Desktop\109_projects\TransVoxia\audio-temp/transcript.csv"
    import csv
    with open(
        file_path,
        "w",
        newline="",
        encoding="utf-8",
    ) as output_file:
        writer = csv.writer(output_file)
        for line in formatted_entries_rounded:
            writer.writerow(line)
    return formatted_entries_rounded, speaker
