from django.urls import path
from . import views
from .views import TaskListAPIView, StopTaskAPIView, ChangeTaskAPIView

app_name = "core"

urlpatterns = [
    path("", views.index, name="index"),
    path("status", views.status_page, name="status_page"),
    path("create_task/", views.create_task, name="create_task"),
    path("api/tasks/", TaskListAPIView.as_view(), name="task-list"),
    path("api/tasks/stop/", StopTaskAPIView.as_view(), name="stop-task"),
    path("api/tasks/change/", ChangeTaskAPIView.as_view(), name="chaneg-task"),
    # ... 其他 URL 路由規則 ...
]
