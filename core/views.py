from django.shortcuts import render

# from social_django.utils import psa
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Task, User
from video.utils import process_video
from .forms import TaskForm
from django.shortcuts import render, redirect
import threading
from video.utils import process_video
from translator.utils import process_deepl
from audio.utils import process_audio


# Create your views here.
def index(request):
    return render(request, "core/index.html")


@csrf_exempt
def create_task(request):
    if request.method == "POST":
        url = request.POST.get("video_url")
        data = {
            "url": url,
            "userID": User.objects.get(email="default@example.com"),
            "target_language": "ZH",
            "voice_selection": "zh-TW-YunJheNeural",
            "mode": "transcript",
            "status": "0",
            # 添加其他需要的字段
        }
        form = TaskForm(data)
        if form.is_valid():
            task = form.save(commit=False)
            task.save()
            threading.Thread(target=process_task, args=(task,)).start()

            return JsonResponse({"status": "success"})
    else:
        return JsonResponse({"status": "fail"})

    return JsonResponse({"status": "error"})


def process_task(task):
    process_video(task)
    process_deepl(task)
    process_audio(task)
