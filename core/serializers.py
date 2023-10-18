from rest_framework import serializers

from core.models import Task, TaskStatus
from django.core.files.storage import default_storage

TRANSCRIPT_STATUS_MAP = {
    TaskStatus.TRANSLATION_PROCESSING: True,
    TaskStatus.VOICE_PROCESSING: True,
    TaskStatus.VOICE_MERGE_PROCESSING: True,
    TaskStatus.TRANSCRIPT_PROCESSING: True,
    TaskStatus.TASK_STOPPED: True,
    TaskStatus.VIDEO_MERGE_PROCESSING: True,
    TaskStatus.TASK_COMPLETED: True,
}
MP3_STATUS_MAP = {
    TaskStatus.VIDEO_MERGE_PROCESSING: True,
    TaskStatus.TASK_COMPLETED: True,
}

MP4_STATUS_MAP = {
    TaskStatus.TASK_COMPLETED: True,
}


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        exclude = ("user",)


class TaskWithTranscriptSerializer(serializers.ModelSerializer):
    speaker_counts = serializers.SerializerMethodField()
    transcript = serializers.SerializerMethodField()
    mp3 = serializers.SerializerMethodField()
    mp4 = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "taskID",
            "target_language",
            "mode",
            "title",
            "speaker_counts",
            "status",
            "request_time",
            "transcript",
            "mp3",
            "mp4",
        ]
    def get_speaker_counts(self, obj):
        return obj.video.speaker_counts
    
    def get_transcript(self, obj):
        if not self.should_return_url(obj, TRANSCRIPT_STATUS_MAP):
            return None
        transcript = obj.transcript  #list
        translated_text = obj.deepl.translated_text #list
        if transcript and translated_text:
            
            if transcript.modified_transcript:
                return transcript.modified_transcript
            for i, trans in enumerate(transcript.transcript):
                trans.append(translated_text[i][3])
            
            return transcript.transcript
        return None

    def get_mp3(self, task):
        if not self.should_return_url(task, MP3_STATUS_MAP):
            return None
        fileName = task.get_file_basename()
        if task.mode in ["video", "audio"]:
            file_path = "translated/audio/" + fileName + ".mp3"
            return default_storage.url(file_path)
        return None

    def get_mp4(self, task):
        if not self.should_return_url(task, MP4_STATUS_MAP):
            return None
        fileName = task.get_file_basename()
        if task.mode == "video":
            file_path = "translated/video/" + fileName + ".mp4"
            return default_storage.url(file_path)
        return None

    def get_status(self, task):
        return task.get_status_display()

    def should_return_url(self, task, status_map):
        return task.status in status_map and status_map[task.status]
