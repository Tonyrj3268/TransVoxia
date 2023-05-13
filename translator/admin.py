from django.contrib import admin

# Register your models here.
from translator.models import Deepl


class Deepl_Info_Admin(admin.ModelAdmin):
    list_display = ("taskID", "translated_text", "status")


admin.site.register(Deepl, Deepl_Info_Admin)
