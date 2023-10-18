from django.db import models


class Video(models.Model):
    file_location = models.CharField(max_length=255, blank=True, null=True)
    length = models.DecimalField(max_digits=6, decimal_places=2, default=10)
    upload_time = models.DateTimeField(auto_now_add=True)
    speaker_counts = models.IntegerField(default=1)
    status = models.BooleanField(default=False)

    def get_task_name(self) -> str:
        return self.task.title if self.task else "No Task"

    get_task_name.short_description = "Task"  # type: ignore


class Transcript(models.Model):
    transcript = models.JSONField(blank=True, null=True)
    modified_transcript = models.JSONField(blank=True, null=True)

    def get_task_name(self) -> str:
        return self.task.title if self.task else "No Task"

    get_task_name.short_description = "Task"  # type: ignore
