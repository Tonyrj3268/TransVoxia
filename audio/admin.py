from django.contrib import admin

# Register your models here.
from audio.models import Play_ht


class Play_ht_Info_Admin(admin.ModelAdmin):
    list_display = (
        "taskID",
        "length_ratio",
        "origin_audio_url",
        "changed_audi_url",
        "status",
    )


admin.site.register(Play_ht, Play_ht_Info_Admin)
