from django import forms
from .models import Task


class TaskForm(forms.ModelForm):
    # def __init__(self, *args, **kwargs):
    #     extra_data = kwargs.pop('extra_data')
    #     super(TaskForm, self).__init__(*args, **kwargs)
    #     for field, value in extra_data.items():
    #         self.fields[field].initial = value
    class Meta:
        model = Task
        fields = ["userID", "target_language", "voice_selection", "mode", "status"]
