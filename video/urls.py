from django.urls import path
from . import views

app_name = 'video'

urlpatterns = [
    path('video_url_input/', views.video_url_input, name='video_url_input'),
    # ... 其他 URL 路由規則 ...
]