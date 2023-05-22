from django.shortcuts import render, get_object_or_404
from django.core.files.storage import default_storage
from django.http import Http404, JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from concurrent.futures import ThreadPoolExecutor
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.parsers import MultiPartParser
from .models import Task, User
from .forms import TaskForm
from .serializers import TaskSerializer
from video.models import Transcript
from video.utils import process_video
from audio.utils import process_audio
from translator.utils import process_deepl
import os
import threading


# Create your views here.
def index(request):
    return render(request, "core/index.html")


def status_page(request):
    return render(request, "core/status.html")


executor = ThreadPoolExecutor(max_workers=5)
task_futures = {}


class TaskListAPIView(APIView):
    parser_classes = (MultiPartParser,)

    @swagger_auto_schema(
        operation_description="Get a list of tasks for a specific user.",
        responses={
            200: "OK",
            404: "User does not exist",
        },
        manual_parameters=[
            openapi.Parameter(
                "email",
                openapi.IN_QUERY,
                description="User's email",
                type=openapi.TYPE_STRING,
            ),
        ],
    )
    def get(self, request):
        email = request.GET.get("email")
        try:
            user = User.objects.get(email=email) if email else None
            tasks = (
                Task.objects.filter(userID=user).order_by("-request_time")
                if user
                else None
            )
            serializer = TaskSerializer(tasks, many=True)
            return Response(serializer.data)
        except User.DoesNotExist:
            raise Http404("User does not exist")

    @swagger_auto_schema(
        operation_description="Create a new task for a specific user.",
        responses={
            200: "Task created successfully",
            500: "Internal Server Error",
        },
        request_body=None,
        manual_parameters=[
            openapi.Parameter(
                name="email",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="User email",
                required=True,
            ),
            openapi.Parameter(
                name="target_language",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Target Language",
                enum=["KO", "EN", "ZH"],
                required=True,
            ),
            openapi.Parameter(
                name="voice_selection",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Voice Selection",
                enum=["ko-KR-Standard-A", "larry", "zh-TW-YunJheNeural"],
                required=True,
            ),
            openapi.Parameter(
                name="mode",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Final Output Mode",
                enum=["transcript", "audio", "video"],
                required=True,
            ),
            openapi.Parameter(
                name="title",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Task Title",
                required=True,
            ),
            openapi.Parameter(
                name="editmode",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_BOOLEAN,
                description="True means the transcript is editable, False means not editable",
                required=True,
            ),
            openapi.Parameter(
                name="file",
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                description="Upload file, for video and audio only",
                required=True,
            ),
        ],
    )
    def post(self, request):
        try:
            email = request.GET.get("email")
            user = get_object_or_404(User, email=email)
            task = Task.objects.create(userID=user)
            task.target_language = request.GET.get("target_language")
            task.voice_selection = request.GET.get("voice_selection")
            task.mode = request.GET.get("mode")
            task.title = request.GET.get("title")
            if request.GET.get("editmode") == "true":
                task.edit_mode = True
            else:
                task.edit_mode = False

            file = request.FILES.get("file")
            if file:
                _, file_extension = os.path.splitext(file.name)
                if file_extension in [".mp4", ".m4a"]:
                    name = default_storage.save("uploads/video/" + file.name, file)
                    task.file = name

                elif file_extension in [".mp3", ".wav"]:
                    name = default_storage.save("uploads/audio/" + file.name, file)
                    task.file = name
                else:
                    raise Exception("File type not supported")
                task.save()
                future = executor.submit(process_task, task)
                task_futures[task.taskID] = future
                return Response(
                    {"msg": "已收到 任務ID: " + str(task.taskID)}, status=status.HTTP_200_OK
                )
            return Response({"msg": "內部問題"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ChangeTaskAPIView(APIView):
    @swagger_auto_schema(
        operation_description="Change a task for a specific user.",
        responses={
            200: "Task changed successfully",
            404: "Task not found",
            400: "Invalid field",
        },
        manual_parameters=[
            openapi.Parameter(
                name="taskID",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Task ID",
                required=True,
            ),
            openapi.Parameter(
                name="field",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Field to change. Acceptable fields: title, transcript.",
                enum=["title", "transcript"],
                required=True,
            ),
            openapi.Parameter(
                name="email",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="User email",
                required=True,
            ),
            openapi.Parameter(
                name="new_value",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="New value for the field",
                required=True,
            ),
        ],
    )
    def post(self, request):
        taskID = request.GET.get("taskID")
        field = request.GET.get("field")
        email = request.GET.get("email")
        new_value = request.GET.get("new_value")

        user = get_object_or_404(User, email=email)

        try:
            task = Task.objects.get(taskID=taskID)
        except Task.DoesNotExist:
            return Response({"error": "Task not found."}, status=404)

        if user == task.userID:
            if field == "title":
                task.title = new_value
                task.save()
            elif field == "transcript":
                tran = get_object_or_404(Transcript, taskID=task)
                tran.transcript = new_value
                tran.save()
            else:
                return Response({"error": "Invalid field."}, status=400)

        return Response({"已修改": field}, status=200)


class StopTaskAPIView(APIView):
    @swagger_auto_schema(
        operation_description="Stop a task for a specific user.",
        responses={
            200: "Task stopped successfully",
            500: "Internal Server Error",
        },
        manual_parameters=[
            openapi.Parameter(
                name="taskID",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Task ID",
                required=True,
            ),
            openapi.Parameter(
                name="email",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="User email",
                required=True,
            ),
        ],
    )
    def post(self, request):
        try:
            taskID = request.GET.get("taskID")
            email = request.GET.get("email")
            user = get_object_or_404(User, email=email)
            task = get_object_or_404(Task, taskID=taskID)
            # 驗證操作的使用者和任務所有者相同
            if user == task.userID and task.status != "-1":
                # future = task_futures[taskID]
                # if future is not None:
                #     future.cancel()
                task.status = "-1"
                task.save()
            return Response({"msg": "已取消"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DownloadFileAPIView(APIView):
    @swagger_auto_schema(
        operation_description="Download specific files for a specific user.",
        responses={
            200: "OK",
            400: "Bad Request",
            401: "Unauthorized",
            404: "File does not exist",
        },
        manual_parameters=[
            openapi.Parameter(
                "taskID",
                openapi.IN_QUERY,
                description="Task ID",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "email",
                openapi.IN_QUERY,
                description="User email",
                type=openapi.TYPE_STRING,
            ),
        ],
    )
    def get(self, request):
        taskID = request.GET.get("taskID")
        email = request.GET.get("email")
        if not taskID or not email:
            return Response("Bad Request", status=status.HTTP_400_BAD_REQUEST)
        task = get_object_or_404(Task, taskID=taskID)
        user = get_object_or_404(User, email=email)

        if user != task.userID:
            return Response("Unauthorized", status=status.HTTP_401_UNAUTHORIZED)

        file_path = "downloads/" + os.path.basename(str(task.file))[:-4] + ".mp3"
        try:
            return FileResponse(open(file_path, "rb"), as_attachment=True)
        except FileNotFoundError:
            return Response("File does not exist", status=status.HTTP_404_NOT_FOUND)


def process_task(task):
    print(f"開始處理任務：{task.taskID}")
    try:
        process_video(task)
        process_deepl(task)
        process_audio(task)
    except Exception as e:
        print(f"強制結束任務：{task.taskID}, 錯誤：{str(e)}")
    print(f"結束處理任務：{task.taskID}")
