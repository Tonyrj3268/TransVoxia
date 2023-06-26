from django.contrib import admin

# Register your models here.
from .models import Play_ht, Play_ht_voices


class Play_ht_Info_Admin(admin.ModelAdmin):
    list_display = (
        "taskID",
        "length_ratio",
        "origin_audio_url",
        "changed_audio_url",
        "status",
    )


class Play_ht_voice_Info_Admin(admin.ModelAdmin):
    list_display = (
        "language",
        "voice",
        "voice_url",
    )


admin.site.register(Play_ht, Play_ht_Info_Admin)
admin.site.register(Play_ht_voices, Play_ht_voice_Info_Admin)
