from django.shortcuts import render
from .models import Video, Transcript
from .utils import generate_transcript_from_url
from django.http import HttpResponse
# Create your views here.
def video_url_input(request):
    if request.method == 'POST':
        url = request.POST.get('video_url')
        trans_text,video_length = generate_transcript_from_url(url)
        result = store_video_info(url,trans_text,video_length)
        # 處理用戶輸入的URL，例如儲存到資料庫或者進行下一步操作
        return HttpResponse('Success') if result else HttpResponse('Failed')
    else:
        return render(request, 'core\input.html')
    
def store_video_info(url,trans_text,video_length):
    new_video = Video.objects.create(url=url,length=video_length)
    transcript = Transcript.objects.create(video=new_video, language='zh-TW', transcript=trans_text)
    return True
