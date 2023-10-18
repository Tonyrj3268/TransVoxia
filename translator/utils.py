from .models import Deepl
import deepl
import traceback
import os
from core.models import Task, TaskStatus
from core.decorators import check_task_status
from django.core.exceptions import ObjectDoesNotExist


@check_task_status(TaskStatus.TRANSLATION_PROCESSING)
def process_deepl(task: Task):
    try:
        texts = task.transcript.transcript
        if task.transcript.modified_transcript:
            texts = task.transcript.modified_transcript
        target_lan = task.target_language

        rows = []
        combined_text = ""
        for segment in texts:
            speaker, begin, end, text = (
                segment[0],
                segment[1],
                segment[2],
                segment[3],
            )
            rows.append([speaker, begin, end, text])
            combined_text += text + "\n" if text != "---" else ""

        translated_combined_text = deepl_tanslator(combined_text, target_lan)
        translated_texts = translated_combined_text.split("\n")

        i = 0
        for row in rows:
            if row[3] != "---":
                row[3] = translated_texts[i]
                i += 1

        updated_json = [
            [row[0],row[1],row[2],row[3]]
            for row in rows
        ]
        deep = Deepl.objects.create(translated_text=updated_json, status=True)
        task.deepl = deep
        task.save()
    except ObjectDoesNotExist as e:
        error_message = str(e) + "\n" + traceback.format_exc()
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
        result = result_translate.text
    except Exception:
        error_message = (
            "Failed to translate text using Deepl.\n" + traceback.format_exc()
        )
        raise Exception(error_message)
    return result
