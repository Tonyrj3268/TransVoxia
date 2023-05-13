from django.db import models
from core.models import Task


class Video(models.Model):
    taskID = models.ForeignKey(Task, on_delete=models.CASCADE)
    file_location = models.CharField(
        max_length=255, default="video-temp/CmwSf7rI2II.m4a"
    )
    length = models.DecimalField(max_digits=6, decimal_places=2, default=10)
    upload_time = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=False)

    def __str__(self):
        return self.taskID.url

    def get_task_url(self):
        """
        獲取當前任務的url
        """
        return self.taskID.url


class Transcript(models.Model):
    taskID = models.ForeignKey(Task, on_delete=models.CASCADE, default=0)
    transcript = models.TextField()

    def __str__(self):
        return f"{self.taskID.url}"
