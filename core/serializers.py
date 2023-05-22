from rest_framework import serializers

from core.models import Task
from video.models import Transcript
from audio.models import Play_ht
from translator.models import Deepl


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        exclude = ("userID",)

    def to_representation(self, instance):
        # 獲取序列化的原始資料
        data = super().to_representation(instance)
        data["transcript"] = ""
        data["translation"] = ""
        if Transcript.objects.filter(taskID=instance).exists():
            data["transcript"] = Transcript.objects.get(taskID=instance).transcript
        if Deepl.objects.filter(taskID=instance).exists():
            data["translation"] = Deepl.objects.get(taskID=instance).translated_text
        return data
