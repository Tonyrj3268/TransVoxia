# Generated by Django 4.2.6 on 2023-10-18 12:15

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="LanguageMapping",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("original_language", models.CharField(max_length=30, unique=True)),
                ("mapped_language", models.CharField(max_length=30)),
            ],
        ),
        migrations.CreateModel(
            name="Play_ht",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("length_ratio", models.FloatField()),
                ("changed_audio_url", models.URLField()),
                ("status", models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name="Play_ht_voices",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("voice", models.CharField(max_length=30, unique=True)),
                ("voice_url", models.URLField(blank=True, null=True)),
                (
                    "language_mapping",
                    models.ForeignKey(
                        blank=True,
                        db_column="language",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="audio.languagemapping",
                        to_field="original_language",
                    ),
                ),
            ],
        ),
    ]
