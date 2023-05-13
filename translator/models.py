from django.db import models
from core.models import Task
# Create your models here.
class Deepl(models.Model):
    taskID = models.ForeignKey(Task, on_delete=models.CASCADE)
    translated_text = models.TextField()
    status = models.BooleanField(default=False)