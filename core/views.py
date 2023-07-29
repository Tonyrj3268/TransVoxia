from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage
from django.http import Http404
from django.db.models import Prefetch
from concurrent.futures import ThreadPoolExecutor
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from .models import Task, TaskStatus
from .serializers import TaskSerializer, TaskWithTranscriptSerializer
from video.models import Transcript
from audio.models import Play_ht_voices
from .utils import (
    process_task_notNeedModify,
    process_task_NeedModify,
    process_task_Remaining,
)
import os
from accounts.models import CustomUser
from rest_framework.pagination import PageNumberPagination
from typing import Dict
from django.db import connection

# Create your views here.
executor = ThreadPoolExecutor(max_workers=4)
task_futures: Dict[int, ThreadPoolExecutor] = {}


class TaskListAPIView(APIView):
    parser_classes = (MultiPartParser,)

    class CustomPagination(PageNumberPagination):
        page_size_query_param = "n"

    @swagger_auto_schema(
        operation_description="Get a list of tasks for a specific user.",
        responses={
            200: openapi.Response("OK", TaskSerializer),
            404: "User does not exist",
        },
        manual_parameters=[
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
    def get(self, request):
        connection.queries.clear()
        user = CustomUser.objects.get(username="root")
        transcripts = Transcript.objects.filter(task__user=user)

        tasks = (
            Task.objects.filter(user=user)
            .order_by("-request_time")
            .prefetch_related(Prefetch("transcript", queryset=transcripts))
        )
        paginator = self.CustomPagination()
        result_page = paginator.paginate_queryset(tasks, request)

        serializer = TaskWithTranscriptSerializer(result_page, many=True)

        return paginator.get_paginated_response(serializer.data)

    @swagger_auto_schema(
        operation_description="Create a new task for a specific user.",
        responses={
            200: "Task created successfully",
            500: "Internal Server Error",
        },
        request_body=None,
        manual_parameters=[
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
                enum=["ko-KR-Standard-B", "Anna", "zh-TW-HsiaoChenNeural"],
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
                name="needModify",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_BOOLEAN,
                description="True means the transcript is need to modify, False means not editable",
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
            target_language = request.GET.get("target_language")
            voice_selection = request.GET.get("voice_selection")
            mode = request.GET.get("mode")
            title = request.GET.get("title")
            needModify = request.GET.get("needModify")
            file = request.FILES.get("file")

            if not all(
                [target_language, voice_selection, mode, title, needModify, file]
            ):
                return Response(
                    {"error": "缺少必要的參數"}, status=status.HTTP_400_BAD_REQUEST
                )
            user = CustomUser.objects.get(username="root")
            play_ht_voice = Play_ht_voices.objects.get(voice=voice_selection)
            task = Task.objects.create(
                user=user,
                target_language=target_language,
                voice_selection=play_ht_voice,
                mode=mode,
                title=title,
                needModify=needModify == "true",
            )

            if file:
                _, file_extension = os.path.splitext(file.name)
                if file_extension in [".mp4", ".mov"]:
                    task.fileLocation = self.handle_file(file, "origin/video/")
                elif file_extension in [".mp3", ".wav", ".m4a"]:
                    task.fileLocation = self.handle_file(file, "origin/audio/")
                else:
                    raise Exception("File type not supported")
                task.save()
                if task.needModify:
                    future = executor.submit(process_task_NeedModify, task)
                else:
                    future = executor.submit(process_task_notNeedModify, task)

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
                name="new_value",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="New value for the field",
                required=True,
            ),
        ],
    )
    # @permission_classes([IsAuthenticated])
    def put(self, request):
        taskID = request.GET.get("taskID")
        field = request.GET.get("field")
        new_value = request.GET.get("new_value")
        user = CustomUser.objects.get(username="root")
        if not all([taskID, field, new_value]):
            return Response(
                {"error": "Missing required fields."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            task = Task.objects.get(taskID=taskID)
        except Task.DoesNotExist:
            return Response({"error": "Task not found."}, status=404)

        if user == task.user:
            if field == "title":
                task.title = new_value
            elif field == "transcript" and task.needModify:
                tran = get_object_or_404(Transcript, taskID=task)
                tran.modified_transcript = new_value
            else:
                return Response({"error": "Invalid field."}, status=400)
            tran.save()
            return Response({"已修改": field}, status=200)
        else:
            return Response(
                {
                    "error": "Forbidden: User does not have permission to access the task"
                },
                status=403,
            )


class StopTaskAPIView(APIView):
    @swagger_auto_schema(
        operation_description="Stop a task for a specific user.",
        responses={
            200: "Task stopped successfully",
            403: "Forbidden: User does not have permission to access the task",
            404: "Not Found: Task not found or already completed",
            500: "Internal Server Error",
        },
    )
    # @permission_classes([IsAuthenticated])
    def post(self, request, taskID):
        try:
            # user = request.user
            user = CustomUser.objects.get(username="root")
            task = get_object_or_404(Task, taskID=taskID)
            if user != task.user:
                return Response({"msg": "無權限操作該任務"}, status=status.HTTP_403_FORBIDDEN)

            if task.status == TaskStatus.TASK_CANCELLED:
                return Response({"msg": "任務已被取消，不進行任何操作"}, status=status.HTTP_200_OK)

            future = task_futures.get(task.taskID)
            if future and not future.done():
                Task.objects.filter(taskID=taskID).update(
                    status=TaskStatus.TASK_CANCELLED
                )
                del task_futures[task.taskID]
                return Response({"msg": "任務已取消"}, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"msg": "無法找到指定的任務或任務已完成"}, status=status.HTTP_404_NOT_FOUND
                )
        except Http404:
            return Response({"msg": "找不到指定的任務"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ContinueTaskAPIView(APIView):
    @swagger_auto_schema(
        operation_description="Continue a task for a specific user.",
        responses={
            200: "Task Continue successfully",
            403: "Forbidden: CustomUser does not have permission to access the task",
            404: "Not Found: Task not found or already completed",
            500: "Internal Server Error",
        },
    )
    def post(self, request, taskID):
        try:
            user = CustomUser.objects.get(username="root")
            task = get_object_or_404(Task, taskID=taskID)
            if user != task.user:
                return Response({"msg": "無權限操作該任務"}, status=status.HTTP_403_FORBIDDEN)

            if task.status == TaskStatus.TASK_CANCELLED:
                return Response({"msg": "任務已被取消，不進行任何操作"}, status=status.HTTP_200_OK)

            if not task.needModify:
                return Response({"msg": "任務不需要編輯，不進行任何操作"}, status=status.HTTP_200_OK)

            self.handle_file(task.fileLocation)
            future = executor.submit(process_task_Remaining, task)
            task_futures[task.taskID] = future

            return Response({"msg": "任務已開始處理"}, status=status.HTTP_200_OK)

        except Http404:
            return Response({"msg": "找不到指定的任務"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response(
                {"msg": f"處理文件時發生錯誤: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @staticmethod
    def handle_file(fileLocation):
        try:
            with default_storage.open(fileLocation, "rb") as f:
                data = f.read()
            with open(fileLocation, "wb") as destination:
                destination.write(data)
        except FileNotFoundError:
            print(f"文件不存在: {fileLocation}")
            raise
        except PermissionError:
            print(f"無權限寫入文件: {fileLocation}")
            raise
        except Exception as e:
            print(f"處理文件時發生未知錯誤: {str(e)}")
            raise
