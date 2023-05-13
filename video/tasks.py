from .utils import *
from django.conf import settings
from celery import shared_task
from .models import Task
import time

@shared_task
def process_unprocessed_urls():
    # 從資料庫中讀取未處理的URL
    urls = Task.objects.filter(processed=False)
    print("開始處理")
    # 檢查是否有未處理的URL
    if urls:
        # 如果有未處理的URL，進行處理
        for url in urls:
            # 處理URL的程式碼

            # 設置URL已處理
            url.processed = True
            url.save()
    else:
        # 如果沒有未處理的URL，等待下一次啟動
        print("開始睡覺")
        time.sleep(settings.UNPROCESSED_URLS_POLL_INTERVAL)