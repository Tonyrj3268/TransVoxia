from django.urls import path
from .views import (
    TaskListAPIView,
    StopTaskAPIView,
    ChangeTaskAPIView,
    DownloadFileAPIView,
)

app_name = "core"

urlpatterns = [
    path("api/tasks/", TaskListAPIView.as_view(), name="task-list"),
    path("api/tasks/stop/", StopTaskAPIView.as_view(), name="stop-task"),
    path("api/tasks/change/", ChangeTaskAPIView.as_view(), name="chaneg-task"),
    # an api to download the task file
    path(
        "api/tasks/download/",
        DownloadFileAPIView.as_view(),
        name="download-file",
    ),
]
