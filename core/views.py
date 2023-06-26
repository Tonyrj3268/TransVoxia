from django.shortcuts import render, get_object_or_404
from django.core.files.storage import default_storage
from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.http import Http404, JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from concurrent.futures import ThreadPoolExecutor
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from .models import Task
from .serializers import TaskSerializer
from video.models import Transcript
from video.utils import process_video, process_synthesis
from audio.utils import process_audio
from translator.utils import process_deepl
import os
import errno
import threading
import base64

# Create your views here.
executor = ThreadPoolExecutor(max_workers=5)
task_futures = {}


class TaskListAPIView(APIView):
    parser_classes = (MultiPartParser,)

    @swagger_auto_schema(
        operation_description="Get a list of tasks for a specific user.",
        responses={
            200: openapi.Response("OK", TaskSerializer),
            404: "User does not exist",
        },
        manual_parameters=[
            openapi.Parameter(
                name="Authorization",
                in_=openapi.IN_HEADER,
                type=openapi.TYPE_STRING,
                description="Token",
                required=True,
            ),
            openapi.Parameter(
                "n",
                openapi.IN_QUERY,
                description="Number of tasks to be returned in one page",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "page",
                openapi.IN_QUERY,
                description="Page number",
                type=openapi.TYPE_INTEGER,
            ),
        ],
    )
    @permission_classes([IsAuthenticated])
    def get(self, request):
        n = int(request.GET.get("n", 0))
        page = int(request.GET.get("page", 1))
        if request.user.is_authenticated:
            user = request.user
            tasks = Task.objects.filter(user=user).order_by("-request_time")
            tasks = tasks[(page - 1) * n : page * n]

            task_results = []
            for task in tasks:
                result = self.get_task_result(task)
                task_results.append(result)

            return Response(task_results)
        else:
            raise PermissionDenied("You must be logged in to view tasks.")

    @staticmethod
    def get_task_result(task):
        result = {"data": TaskSerializer(task).data}
        fileName = task.fileLocation.split("/")[2].split(".")[0]
        base_url = os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET_OPEN_URL") + "translated/"
        transcript = Transcript.objects.get(taskID=task).transcript

        result["transcript"] = transcript
        if task.mode in ["video", "audio"]:
            result["mp3"] = base_url + "audio/" + fileName + ".mp3"
            if task.mode == "video":
                result["mp4"] = base_url + "video/" + fileName + ".mp4"

        return result

    @swagger_auto_schema(
        operation_description="Create a new task for a specific user.",
        responses={
            200: "Task created successfully",
            500: "Internal Server Error",
        },
        request_body=None,
        manual_parameters=[
            openapi.Parameter(
                name="Authorization",
                in_=openapi.IN_HEADER,
                type=openapi.TYPE_STRING,
                description="Bearer <JWT Token>",
                required=True,
            ),
            openapi.Parameter(
                name="target_language",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Target Language",
                enum=["KO", "EN-US", "ZH"],
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
    @permission_classes([IsAuthenticated])
    def post(self, request):
        try:
            user = request.user
            task = Task.objects.create(
                user=user,
                target_language=request.GET.get("target_language"),
                voice_selection=request.GET.get("voice_selection"),
                mode=request.GET.get("mode"),
                title=request.GET.get("title"),
                edit_mode=request.GET.get("editmode") == "true",
            )

            file = request.FILES.get("file")
            if file:
                _, file_extension = os.path.splitext(file.name)
                if file_extension in [".mp4", ".mov"]:
                    task.fileLocation = self.handle_file(file, "origin/video/")
                elif file_extension in [".mp3", ".wav", ".m4a"]:
                    task.fileLocation = self.handle_file(file, "origin/audio/")
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

    @staticmethod
    def handle_file(file, location):
        """
        check if file name already exists, if so, add suffix to the file name,
        then save the file to the google cloud and the local location.
        """
        filename = default_storage.get_available_name(location + file.name)
        name = default_storage.save(filename, file)
        with open(name, "wb") as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        return name


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
                name="Authorization",
                in_=openapi.IN_HEADER,
                type=openapi.TYPE_STRING,
                description="Bearer <JWT Token>",
                required=True,
            ),
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
                name="new_value",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="New value for the field",
                required=True,
            ),
        ],
    )
    @permission_classes([IsAuthenticated])
    def post(self, request):
        taskID = request.GET.get("taskID")
        field = request.GET.get("field")
        new_value = request.GET.get("new_value")

        user = request.user

        try:
            task = Task.objects.get(taskID=taskID)
        except Task.DoesNotExist:
            return Response({"error": "Task not found."}, status=404)

        if user == task.user:
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
                name="Authorization",
                in_=openapi.IN_HEADER,
                type=openapi.TYPE_STRING,
                description="Bearer <JWT Token>",
                required=True,
            ),
            openapi.Parameter(
                name="taskID",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Task ID",
                required=True,
            ),
        ],
    )
    @permission_classes([IsAuthenticated])
    def post(self, request):
        try:
            taskID = request.GET.get("taskID")
            user = request.user
            task = get_object_or_404(Task, taskID=taskID)
            # 驗證操作的使用者和任務所有者相同
            if user == task.user:
                if task.status == "-1":
                    return Response(
                        {"msg": "任務已被取消，不進行任何操作"}, status=status.HTTP_200_OK
                    )
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
                name="Authorization",
                in_=openapi.IN_HEADER,
                type=openapi.TYPE_STRING,
                description="Bearer <JWT Token>",
                required=True,
            ),
            openapi.Parameter(
                "taskID",
                openapi.IN_QUERY,
                description="Task ID",
                type=openapi.TYPE_STRING,
            ),
        ],
    )
    @permission_classes([IsAuthenticated])
    def get(self, request):
        taskID = request.GET.get("taskID")
        if not taskID:
            return Response("Bad Request", status=status.HTTP_400_BAD_REQUEST)
        task = get_object_or_404(Task, taskID=taskID)
        user = request.user

        if user != task.user:
            return Response("Unauthorized", status=status.HTTP_401_UNAUTHORIZED)
        if task.mode == "video":
            file_path = (
                "translated/video/"
                + os.path.basename(str(task.fileLocation))[:-4]
                + ".mp4"
            )
        elif task.mode == "audio":
            file_path = (
                "translated/audio/"
                + os.path.basename(str(task.fileLocation))[:-4]
                + ".mp3"
            )
        try:
            file_url = default_storage.url(file_path)
            return JsonResponse({"file_url": file_url})
        except FileNotFoundError:
            return Response("File does not exist", status=status.HTTP_404_NOT_FOUND)


def process_task(task):
    print(f"開始處理任務：{task.taskID}")
    status = "4"
    try:
        process_video(task)
        process_deepl(task)
        process_audio(task)
        if task.mode == "video":
            process_synthesis(task)

    except Exception as e:
        status = "-1"
        print(f"強制結束任務：{task.taskID}, 錯誤：{str(e)}")

    audioFilePath = (task.fileLocation).split("/")[-1].split(".")[0] + ".mp3"
    videoFilePath = (task.fileLocation).split("/")[-1].split(".")[0] + ".mp4"
    file_paths = [
        "translated/audio/" + audioFilePath,
        task.fileLocation,
        "translated/video/" + videoFilePath,
    ]
    for file_path in file_paths:
        try:
            os.remove(file_path)
            print(f"已成功刪除檔案：{file_path}")
        except OSError as e:
            if e.errno == errno.ENOENT:  # 檔案不存在的錯誤
                print(f"檔案不存在，無法刪除: {file_path}")
            elif e.errno == errno.EACCES:  # 檔案或目錄無法存取的錯誤
                print(f"檔案正在被使用，無法刪除: {file_path}")
            else:
                print(f"刪除檔案時發生錯誤: {file_path} - {str(e)}")

    task.status = status
    task.save()
    print(f"結束處理任務：{task.taskID}")
