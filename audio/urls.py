from django.urls import path
from . import views
from .views import (
    LanguageListView,
    VoicesListView,
)

app_name = "audio"

urlpatterns = [
    path("language/", LanguageListView.as_view(), name="language-list"),
    path("voices/", VoicesListView.as_view(), name="voice-list"),
]
