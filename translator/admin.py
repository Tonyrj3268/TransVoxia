from django.contrib import admin

# Register your models here.
from translator.models import Deepl


class Deepl_Info_Admin(admin.ModelAdmin):
    list_display = ("get_task_name", "translated_text", "status")

    def get_task_name(self, obj):
        return obj.task.title if obj.task else "No Task"

    get_task_name.short_description = "Task"


admin.site.register(Deepl, Deepl_Info_Admin)
