from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.index, name='index'),
    path('create_task/', views.create_task, name='create_task'),
    # ... 其他 URL 路由規則 ...
]