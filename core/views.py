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
from .serializers import TaskSerializer
from rest_framework.views import APIView
from rest_framework.response import Response

# Create your views here.
def index(request):
    return render(request, "core/index.html")
def status_page(request):
    return render(request, "core/status.html")

class TaskListAPIView(APIView):
    def get(self, request):
        email = request.GET.get('email')
        if email:
            user = User.objects.filter(email=email).first()
            if user:
                tasks = Task.objects.filter(userID=user)
            else:
                tasks = Task.objects.none()
        else:
            tasks = Task.objects.all()

        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)
    
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
