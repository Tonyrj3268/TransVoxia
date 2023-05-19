from django.contrib import admin
from .models import User, Task


class User_Info_Admin(admin.ModelAdmin):
    list_display = (
        "userID",
        "membership_level",
        "expiration_date",
        "email",
        "password",
    )


class Task_Info_Admin(admin.ModelAdmin):
    list_display = (
        "taskID",
        "userID",
        "file",
        "request_time",
        "target_language",
        "voice_selection",
        "mode",
        "status",
        "edit_mode",
    )


admin.site.register(User, User_Info_Admin)
admin.site.register(Task, Task_Info_Admin)
