from django.shortcuts import render
from .models import Video, Transcript
from .utils import generate_transcript_from_url

# Create your views here.
def video_url_input(request):
    if request.method == 'POST':
        url = request.POST.get('video_url')
        result = process_video_url(url)
        # 處理用戶輸入的URL，例如儲存到資料庫或者進行下一步操作
        return render(request, 'core\success.html')
    else:
        return render(request, 'core\input.html')
    
def process_video_url(url):
    trans_text,video_length = generate_transcript_from_url(url)
    new_video = Video.objects.create(url=url,length=video_length)
    transcript = Transcript.objects.create(video=new_video, language='zh-TW', transcript=trans_text)
    return True
