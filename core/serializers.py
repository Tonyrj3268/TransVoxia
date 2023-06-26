from rest_framework import serializers

from core.models import Task
from video.models import Transcript
from audio.models import Play_ht
from translator.models import Deepl


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        exclude = ("user",)
