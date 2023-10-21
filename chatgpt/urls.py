from django.urls import path

from .views import ChatViewSet, TranslatorChatgptView

urlpatterns = [
    path("chatgpt/", ChatViewSet.as_view(), name="chatgpt"),
    path(
        "translator_chatgpt/<str:taskID>/",
        TranslatorChatgptView.as_view(),
        name="translator_chatgpt",
    ),
]
