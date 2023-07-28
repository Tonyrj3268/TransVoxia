from django.db import models


# Create your models here.
class Deepl(models.Model):
    translated_text = models.TextField()
    status = models.BooleanField(default=False)

    def get_task_name(self) -> str:
        return self.task.title if self.task else "No Task"

    get_task_name.short_description = "Task"  # type: ignore
