from django.shortcuts import render

# from social_django.utils import psa
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Task, User
from video.utils import process_video
from .forms import TaskForm
from django.shortcuts import render, redirect
import threading
from video.utils import process_video
from translator.utils import process_deepl
from audio.utils import process_audio


# Create your views here.
def index(request):
    return render(request, "core/index.html")


@csrf_exempt
def create_task(request):
    if request.method == "POST":
        url = request.POST.get("video_url")
        data = {
            "url": url,
            "userID": User.objects.get(email="default@example.com"),
            "target_language": "ZH",
            "voice_selection": "zh-TW-YunJheNeural",
            "mode": "transcript",
            "status": "0",
            # 添加其他需要的字段
        }
        form = TaskForm(data)
        if form.is_valid():
            task = form.save(commit=False)
            task.save()
            threading.Thread(target=process_task, args=(task,)).start()

            return JsonResponse({"status": "success"})
    else:
        return JsonResponse({"status": "fail"})

    return JsonResponse({"status": "error"})


def process_task(task):
    process_video(task)
    process_deepl(task)
    process_audio(task)


"""
async def create_task(request):
    # 從請求中獲取URL
    url = request.POST.get('video_url')
    
    # 將URL記錄到資料庫
    # 狀態設置為未完成
    try:
        user = User.objects.get(email="default@example.com")
        task = {'userID':user, 'url':url, 'target_language':'zh-TW', 'voice_selection':'', 'mode':'逐字稿', 'status':'Status 0'}
        video = {'file_location' : url,}
        async with transaction.atomic():
            task_obj = Task.objects.create(**task)
            video['taskID'] = task_obj
            Video.objects.create(**video)
        # 啟動一個非同步任務處理視頻
        asyncio.create_task(process_video())

        # 創建任務成功，返回成功的響應
        return JsonResponse({'status': 'success'})
    except Exception as e:
        # 創建任務失敗，返回錯誤的響應
        return JsonResponse({'status': 'error', 'message': str(e)})
"""
