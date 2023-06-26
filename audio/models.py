from django.db import models
from core.models import Task


# Create your models here.
class Play_ht(models.Model):
    taskID = models.ForeignKey(Task, on_delete=models.CASCADE)
    length_ratio = models.FloatField()
    origin_audio_url = models.URLField()
    changed_audio_url = models.URLField()
    status = models.BooleanField(default=False)


class Play_ht_voices(models.Model):
    language = models.CharField(max_length=30)
    voice = models.CharField(max_length=30)
    voice_url = models.URLField(blank=True, null=True)
