from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.input, name='input'),
    # ... 其他 URL 路由規則 ...
]