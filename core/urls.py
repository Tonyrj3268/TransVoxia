from django.urls import path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from .views import (
    ContinueTaskAPIView,
    StopTaskAPIView,
    TaskListAPIView,
    GetIncompleteAPIView,
)

schema_view = get_schema_view(
    openapi.Info(
        title="Trans Voxia API",
        default_version="v1",
        description="Trans Voxia API description",
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
    path("stop_task/<str:taskID>/", StopTaskAPIView.as_view()),
    path("continue_task/<str:taskID>/", ContinueTaskAPIView.as_view()),
    path("get_incomplete/<str:taskID>/", GetIncompleteAPIView.as_view()),
]
