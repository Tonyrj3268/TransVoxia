from django.shortcuts import render
from django.core.files.storage import default_storage
from django.http import Http404

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
from rest_framework import status
from concurrent.futures import ThreadPoolExecutor
from django.shortcuts import get_object_or_404


# Create your views here.
def index(request):
    return render(request, "core/index.html")


def status_page(request):
    return render(request, "core/status.html")


executor = ThreadPoolExecutor(max_workers=5)
task_futures = {}


class TaskListAPIView(APIView):
    def get(self, request):
        email = request.GET.get("email")
        try:
            user = User.objects.get(email=email) if email else None
            tasks = Task.objects.filter(userID=user) if user else None
            serializer = TaskSerializer(tasks, many=True)
            return Response(serializer.data)
        except User.DoesNotExist:
            raise Http404("User does not exist")

    def post(self, request):
        try:
            email = request.data.get("email")
            user = get_object_or_404(User, email=email)
            task = Task.objects.create(userID=user)
            task.target_language = request.data.get("target_language")
            task.voice_selection = request.data.get("voice_selection")
            task.mode = request.data.get("mode")
            task.title = request.data.get("title")
            task.edit_mode = request.data.get("editmode")

            file = request.FILES.get("file")
            if file:
                filename = default_storage.save("uploads/" + file.name, file)
                task.file = filename  # 將文件路徑保存到數據庫字段中

            task.save()
            # future = executor.submit(process_task, task)
            # task_futures[task.taskID] = future
            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class StopTaskAPIView(APIView):
    def post(self, request):
        try:
            task_id = request.data.get("task_id")
            email = request.data.get("email")
            user = get_object_or_404(User, email=email)
            task = get_object_or_404(Task, taskID=task_id)
            # 驗證操作的使用者和任務所有者相同
            if user == task.userID and task.status != "-1":
                future = task_futures.get(task_id)
                if future is not None:
                    future.cancel()
                task.status = "-1"
                task.save()
            return Response({"msg": "已取消"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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
