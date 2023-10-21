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
        "mode",
        "status",
    )
    readonly_fields = (
        "user",
        "fileLocation",
        "request_time",
        "target_language",
        "mode",
        "status",
        "transcript",
        "video",
        "deepl",
        "playht",
    )


admin.site.register(Task, Task_Info_Admin)
