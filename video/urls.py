from django.urls import path
from . import views

app_name = 'video'

urlpatterns = [
    path('transcript', views.generate_transcript),
    # ... 其他 URL 路由規則 ...
]