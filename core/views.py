from django.shortcuts import render

# Create your views here.
def input(request):
    return render(request, 'core/input.html')

def video_url_input(request):
    if request.method == 'POST':
        url = request.POST.get('video_url')
        # 處理用戶輸入的URL，例如儲存到資料庫或者進行下一步操作
        return render(request, 'success.html', {'url': url})
    else:
        return render(request, 'input.html')