from rest_framework import serializers

from core.models import Task
from django.core.files.storage import default_storage


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        exclude = ("user",)


class TaskWithTranscriptSerializer(serializers.ModelSerializer):
    transcript = serializers.SerializerMethodField()
    mp3 = serializers.SerializerMethodField()
    mp4 = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "taskID",
            "target_language",
            "voice_selection",
            "mode",
            "title",
            "needModify",
            "status",
            "request_time",
            "transcript",
            "mp3",
            "mp4",
        ]

    def get_transcript(self, obj):
        transcript = obj.transcript_set.first()
        if transcript:
            if transcript.modified_transcript:
                return transcript.modified_transcript
            else:
                return transcript.transcript
        return None

    def get_mp3(self, task):
        fileName = task.fileLocation.split("/")[2].split(".")[0]
        if task.mode in ["video", "audio"]:
            file_path = "translated/audio/" + fileName + ".mp3"
            return default_storage.url(file_path)
        return None

    def get_mp4(self, task):
        fileName = task.fileLocation.split("/")[2].split(".")[0]
        if task.mode == "video":
            file_path = "translated/video/" + fileName + ".mp4"
            return default_storage.url(file_path)
        return None

    def get_status(self, obj):
        return obj.get_status_display()
