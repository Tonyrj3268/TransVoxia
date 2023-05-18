from rest_framework import serializers

from core.models import Task
from video.models import Transcript
from audio.models import Play_ht
from translator.models import Deepl


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        exclude = ("taskID",)

    def to_representation(self, instance):
        # 獲取序列化的原始資料
        data = super().to_representation(instance)

        # 移除 'id' 欄位
        data.pop("taskID")

        data["transcript"] = Transcript.objects.get(taskID=instance).transcript
        data["translation"] = Deepl.objects.get(taskID=instance).translated_text

        if data["mode"] == "audio":
            data["audio"] = Play_ht.objects.get(taskID=instance).changed_audio_url
        elif data["mode"] == "video":
            pass

        return data
