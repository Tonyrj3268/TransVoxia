from django.contrib import admin

# Register your models here.
from video.models import *


class Video_Info_Admin(admin.ModelAdmin):
    list_display = ("get_task_name", "file_location", "length", "upload_time","speaker_counts", "status")


class Transcript_Admin(admin.ModelAdmin):
    list_display = ("get_task_name", "transcript")


admin.site.register(Video, Video_Info_Admin)
admin.site.register(Transcript, Transcript_Admin)
