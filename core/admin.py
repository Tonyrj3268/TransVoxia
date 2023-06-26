from django.contrib import admin
from .models import Task


class Task_Info_Admin(admin.ModelAdmin):
    list_display = (
        "taskID",
        "user",
        "title",
        "fileLocation",
        "request_time",
        "target_language",
        "voice_selection",
        "mode",
        "status",
        "edit_mode",
    )


admin.site.register(Task, Task_Info_Admin)
