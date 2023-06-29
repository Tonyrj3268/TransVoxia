from .models import Deepl
import deepl
from video.models import Transcript
import os
from core.models import Task, TaskStatus
from core.decorators import check_task_status


@check_task_status
def process_deepl(task: Task):
    if task:
        dpl = Deepl.objects.create(taskID=task)
        text = Transcript.objects.get(taskID=task).transcript
        target_lan = task.target_language
        prompt = deepl_tanslator(text, target_lan, origin_lan=None)
        dpl.translated_text = prompt
        dpl.status = True
        dpl.save()
        task.status = TaskStatus.TRANSLATION_COMPLETED
        task.save()

        print("結束處理deepl")
    else:
        # 如果沒有未處理的URL，等待下一次啟動
        print("開始睡覺")


def deepl_tanslator(text, target_lan, origin_lan=None):
    auth_key = os.getenv("DEEPL_API_KEY")  # Replace with your key
    translator = deepl.Translator(auth_key)
    result_translate = translator.translate_text(text, target_lang=target_lan)
    prompt = result_translate.text
    print("----------翻譯已完成----------")
    return prompt
