from .models import Deepl
import deepl
from video.models import Transcript
import os
from core.models import Task, TaskStatus
from core.decorators import check_task_status


@check_task_status(TaskStatus.TRANSLATION_PROCESSING)
def process_deepl(task: Task):
    text = Transcript.objects.get(taskID=task).transcript
    target_lan = task.target_language
    prompt = deepl_tanslator(text, target_lan)
    Deepl.objects.create(taskID=task, translated_text=prompt, status=True)


def deepl_tanslator(text, target_lan, origin_lan=None):
    auth_key = os.getenv("DEEPL_API_KEY")  # Replace with your key
    translator = deepl.Translator(auth_key)
    result_translate = translator.translate_text(text, target_lang=target_lan)
    prompt = result_translate.text
    return prompt
