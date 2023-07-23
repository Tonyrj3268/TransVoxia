from django.db import models


class Video(models.Model):
    file_location = models.CharField(max_length=255, blank=True, null=True)
    length = models.DecimalField(max_digits=6, decimal_places=2, default=10)
    upload_time = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=False)


class Transcript(models.Model):
    transcript = models.TextField(blank=True, null=True)
    modified_transcript = models.TextField(blank=True, null=True)
