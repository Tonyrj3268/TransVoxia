from django.urls import path
from . import views
from .views import (
    ChatViewSet,
)
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


urlpatterns = [
    path("chatgpt/", ChatViewSet.as_view(), name="chatgpt"),
]
