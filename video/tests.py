import unittest
from django.test import TestCase, Client
from django.urls import reverse
from .models import Video, Transcript
from .utils import *
from .views import *

class VideoTestCase(TestCase):
    
    def setUp(self):
        self.url = 'https://www.youtube.com/watch?v=CmwSf7rI2II'
        self.language = 'zh-TW'
        self.path =  "video-temp/"+self.url.split("watch?v=")[1].split("&")[0]+".m4a"
        self.transcript = "Whatever you are into, San Jacinto College is into your success. Learn more at SanJack.edu."
        self.length = 10
    def tearDown(self):
        # 刪除檔案
        if os.path.exists(self.path):
            os.remove(self.path)

    #測試是否下載成功
    def test_download_youtube(self):
        download_youtube(self.url)
        self.assertIsNotNone(self.path)
        self.assertTrue(os.path.exists(self.path))
        self.assertGreater(os.path.getsize(self.path), 0)
    #測試是否文字稿成功生成、影片長度生成
    def test_convert_to_text(self):
        text, length = generate_transcript_from_url(self.url)
        self.assertIsNotNone(text)
        self.assertIsInstance(text, str)
        self.assertGreater(len(text), len(self.transcript)-10)
        self.assertGreater(length,0)
    #測試是否文字稿、影片長度成功儲存
    def test_store_video_info(self):
        store_video_info(self.url,self.transcript,self.length)
        saved_video = Video.objects.get(url=self.url)
        saved_transcript = Transcript.objects.get(video=saved_video)
        self.assertEqual(saved_video.length, self.length)
        self.assertEqual(saved_transcript.transcript, self.transcript)
    
    def test_whole_process(self):
        c = Client()
        response = c.post(reverse('video:video_url_input'), {'video_url': self.url})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), 'Success')
        saved_video = Video.objects.get(url=self.url)
        saved_transcript = Transcript.objects.get(video=saved_video)
        self.assertIsNotNone(saved_video.length)
        self.assertIsNotNone(saved_video.upload_time)
        self.assertTrue(os.path.exists(self.path))
        self.assertEqual(saved_video.length, self.length)
        self.assertGreater(len(saved_transcript.transcript), len(self.transcript)-10)