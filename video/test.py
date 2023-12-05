# from .utils import get_transcript
from syrupy.assertion import SnapshotAssertion
import os
import whisperx

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def test_get_transcript(snapshot: SnapshotAssertion):
    file_path = os.path.join(BASE_DIR, "data", "youtube_1.mp4")
    snapshot.assert_match(get_transcript(file_path))


def get_transcript(file_path: str) -> list:
    device = "cuda"
    batch_size = 16  # reduce if low on GPU mem
    compute_type = "float16"  # change to "int8" if low on GPU mem (may reduce accuracy)

    model = whisperx.load_model("large-v3", device, compute_type=compute_type)
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
    hugging_face_token = os.getenv("HUGGING_FACE_TOKEN", None)
    diarize_model = whisperx.DiarizationPipeline(
        model_name="pyannote/speaker-diarization-3.1",
        use_auth_token=hugging_face_token,
        device=device,
    )
    diarize_segments = diarize_model(audio)

    result = whisperx.assign_word_speakers(diarize_segments, result)
    return result["segments"]


if __name__ == "__main__":
    file_path = os.path.join(BASE_DIR, "data", "youtube_1.mp4")
    print(get_transcript(file_path))
