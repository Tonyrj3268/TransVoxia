from django.shortcuts import render, get_object_or_404
from django.core.files.storage import default_storage
from django.http import Http404, JsonResponse, FileResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Task, User
from .serializers import TaskSerializer


class TaskListAPIView(APIView):
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
            tasks = Task.objects.filter(userID=user) if user else None
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
                in_=openapi.IN_QUERY,
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
                task.file = "uploads/" + file.name  # 將文件路徑保存到數據庫字段中
            fake_status = {"transcript": "2", "audio": "3", "video": "4"}
            task.status = fake_status[task.mode]
            task.save()
            return Response({"msg": "已收到"}, status=status.HTTP_200_OK)
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
                task.transcript = new_value
                task.save()
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

        file_path = '../video-temp/30_complete_audio_new.mp3'
        try:
            return FileResponse(open(file_path, "rb"), as_attachment=True)
        except FileNotFoundError:
            print("not found")
            return Response("File does not exist", status=status.HTTP_404_NOT_FOUND)
