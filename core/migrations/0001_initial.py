# Generated by Django 4.2.6 on 2023-10-18 12:25

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("translator", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("video", "0001_initial"),
        ("audio", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Task",
            fields=[
                ("taskID", models.AutoField(primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=255)),
                ("fileLocation", models.CharField(blank=True, max_length=255)),
                ("request_time", models.DateTimeField(auto_now_add=True)),
                ("target_language", models.CharField(max_length=255)),
                ("voice_selection", models.TextField(blank=True, null=True)),
                (
                    "mode",
                    models.CharField(
                        choices=[
                            ("transcript", "逐字稿"),
                            ("audio", "語音"),
                            ("video", "影片"),
                        ],
                        max_length=50,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("0", "未處理"),
                            ("1", "文字稿生成中"),
                            ("2", "Deepl翻譯中"),
                            ("3", "Play.ht語音生成中"),
                            ("4", "語音合成中"),
                            ("5", "影片合成中"),
                            ("6", "任務停止，等待用戶繼續"),
                            ("7", "任務完成"),
                            ("-1", "任務失敗"),
                            ("-2", "任務取消"),
                            ("None", "N/A"),
                        ],
                        default="0",
                        max_length=50,
                    ),
                ),
                ("needModify", models.BooleanField(default=False)),
                (
                    "deepl",
                    models.OneToOneField(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="translator.deepl",
                    ),
                ),
                (
                    "playht",
                    models.OneToOneField(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="audio.play_ht",
                    ),
                ),
                (
                    "transcript",
                    models.OneToOneField(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="video.transcript",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "video",
                    models.OneToOneField(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="video.video",
                    ),
                ),
            ],
        ),
    ]
