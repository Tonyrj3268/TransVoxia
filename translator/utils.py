from .models import Deepl
import deepl
import traceback
from video.models import Transcript
import os
from core.models import Task, TaskStatus
from core.decorators import check_task_status


@check_task_status(TaskStatus.TRANSLATION_PROCESSING)
def process_deepl(task: Task):
    try:
        text = Transcript.objects.get(taskID=task).transcript
        target_lan = task.target_language
        prompt = deepl_tanslator(text, target_lan)
        Deepl.objects.create(taskID=task, translated_text=prompt, status=True)
    except Transcript.DoesNotExist:
        error_message = (
            "Transcript for this task does not exist.\n" + traceback.format_exc()
        )
        raise Exception(error_message)
    except Exception:
        error_message = (
            "Failed to process Deepl translation.\n" + traceback.format_exc()
        )
        raise Exception(error_message)


def deepl_tanslator(text, target_lan):
    deepl_api_key = os.getenv("DEEPL_API_KEY", None)
    if deepl_api_key is None:
        raise Exception("DEEPL_API_KEY is not set in the environment variables.")
    try:
        translator = deepl.Translator(deepl_api_key)
        result_translate = translator.translate_text(text, target_lang=target_lan)
        prompt = result_translate.text
    except Exception:
        error_message = (
            "Failed to translate text using Deepl.\n" + traceback.format_exc()
        )
        raise Exception(error_message)
    return prompt
