from django.contrib import admin

# Register your models here.
from .models import Play_ht, Play_ht_voices, LanguageMapping


@admin.register(Play_ht)
class Play_ht_Info_Admin(admin.ModelAdmin):
    list_display = (
        "get_task_name",
        "length_ratio",
        "changed_audio_url",
        "status",
    )

    def get_task_name(self, obj):
        return obj.task.title if obj.task else "No Task"

    get_task_name.short_description = "Task"  # type: ignore


@admin.register(Play_ht_voices)
class Play_ht_voicesAdmin(admin.ModelAdmin):
    list_display = ["voice", "voice_url", "language_mapping"]  # 在列表视图中显示的字段
    list_filter = ["language_mapping"]  # 添加过滤器，可以按照`language_mapping`字段筛选
    search_fields = ["voice"]  # 添加搜索字段，可以根据`voice`字段搜索


@admin.register(LanguageMapping)
class LanguageMapping_Info_Admin(admin.ModelAdmin):
    list_display = (
        "original_language",
        "mapped_language",
    )
