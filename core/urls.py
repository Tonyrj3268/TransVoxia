from django.urls import path
from . import views
from .views import (
    TaskListAPIView,
    StopTaskAPIView,
    ChangeTaskAPIView,
    DownloadFileAPIView,
)
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Trans Voxia API",
        default_version="v1",
        description="Trans Voxia API description",
        # terms_of_service="https://www.google.com/policies/terms/",
        # contact=openapi.Contact(email="contact@mysite.com"),
        # license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)
app_name = "core"

urlpatterns = [
    path(
        "",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("tasks/", TaskListAPIView.as_view(), name="task-list"),
    path("tasks/stop/", StopTaskAPIView.as_view(), name="stop-task"),
    path("tasks/change/", ChangeTaskAPIView.as_view(), name="chaneg-task"),
    # an api to download the task file
    path(
        "tasks/download/",
        DownloadFileAPIView.as_view(),
        name="download-file",
    ),
]
