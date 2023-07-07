from django.db import models
from core.models import Task


class Video(models.Model):
    taskID = models.ForeignKey(Task, on_delete=models.CASCADE)
    file_location = models.CharField(max_length=255, blank=True, null=True)
    length = models.DecimalField(max_digits=6, decimal_places=2, default=10)
    upload_time = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=False)


class Transcript(models.Model):
    taskID = models.ForeignKey(Task, on_delete=models.CASCADE, default=0)
    transcript = models.TextField()
