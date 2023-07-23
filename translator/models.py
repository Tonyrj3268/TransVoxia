from django.db import models


# Create your models here.
class Deepl(models.Model):
    translated_text = models.TextField()
    status = models.BooleanField(default=False)
