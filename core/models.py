from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class TaskStatus(models.TextChoices):
    UNPROCESSED = "0", _("未處理")
    TRANSCRIPT_COMPLETED = "1", _("文字稿生成完成")
    TRANSLATION_COMPLETED = "2", _("Deepl翻譯完成")
    VOICE_GENERATION_COMPLETED = "3", _("Play.ht語音生成完成")
    TASK_COMPLETED = "4", _("任務完成")
    TASK_FAILED = "-1", _("任務失敗")
    TASK_CANCELLED = "-2", _("任務取消")
    NA = None, _("N/A")


class Task(models.Model):
    taskID = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    fileLocation = models.CharField(max_length=255, blank=True)
    request_time = models.DateTimeField(auto_now_add=True)
    target_language = models.CharField(max_length=255)
    # make a list with tuples and contains these languages with key and same value， ["ko-KR-Standard-A", "larry", "zh-TW-YunJheNeural"]
    voice_CHOICES = [
        ("ko-KR-Standard-A", "ko-KR-Standard-A"),
        ("larry", "larry"),
        ("zh-TW-YunJheNeural", "zh-TW-YunJheNeural"),
    ]
    voice_selection = models.CharField(choices=voice_CHOICES, max_length=255)

    MODE_CHOICES = [("transcript", "逐字稿"), ("audio", "語音"), ("video", "影片")]
    mode = models.CharField(choices=MODE_CHOICES, max_length=50)
    status = models.CharField(
        choices=TaskStatus.choices, max_length=50, default=TaskStatus.UNPROCESSED
    )
    needModify = models.BooleanField(default=False)
