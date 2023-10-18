from django.db import models


# Create your models here.
class Play_ht(models.Model):
    changed_audio_url = models.URLField()
    status = models.BooleanField(default=False)


class LanguageMapping(models.Model):
    original_language = models.CharField(max_length=30, unique=True)
    mapped_language = models.CharField(max_length=30)

    def __str__(self):
        return self.mapped_language


class Play_ht_voices(models.Model):
    language_mapping = models.ForeignKey(
        LanguageMapping,
        on_delete=models.CASCADE,
        to_field="original_language",
        db_column="language",
        blank=True,
        null=True,
    )
    voice = models.CharField(max_length=30, unique=True)
    voice_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.voice
