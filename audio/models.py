from django.db import models
from core.models import Task


# Create your models here.
class Play_ht(models.Model):
    taskID = models.ForeignKey(Task, on_delete=models.CASCADE)
    length_ratio = models.FloatField()
    origin_audio_url = models.URLField()
    changed_audio_url = models.URLField()
    status = models.BooleanField(default=False)
