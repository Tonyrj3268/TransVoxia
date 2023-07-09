from django.urls import path
from .views import (
    ChatViewSet,
)


urlpatterns = [
    path("chatgpt/", ChatViewSet.as_view(), name="chatgpt"),
]
