from django.contrib import admin

# Register your models here.
from video.models import *


class Video_Info_Admin(admin.ModelAdmin):
    list_display = ("get_task_name", "file_location", "length", "upload_time", "status")

    def get_task_name(self, obj):
        return obj.task.title if obj.task else "No Task"

    get_task_name.short_description = "Task"


class Transcript_Admin(admin.ModelAdmin):
    list_display = ("get_task_name", "transcript")

    def get_task_name(self, obj):
        return obj.task.title if obj.task else "No Task"

    get_task_name.short_description = "Task"


admin.site.register(Video, Video_Info_Admin)
admin.site.register(Transcript, Transcript_Admin)
