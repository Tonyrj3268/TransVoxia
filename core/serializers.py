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

    class Meta:
        model = Task
        fields = [
            "taskID",
            "target_language",
            "voice_selection",
            "mode",
            "title",
            "edit_mode",
            "transcript",
            "mp3",
            "mp4",
            "request_time",
        ]

    def get_transcript(self, obj):
        transcript = (
            obj.transcript_set.first()
        )  # adjust this line based on your relationship
        return transcript.transcript if transcript else None

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
