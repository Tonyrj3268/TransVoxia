from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from .models import *
from .utils import *
from core.models import *
import datetime


class TestDownloadYoutube(TestCase):
    @patch("video.utils.YoutubeDL")
    def test_download_youtube(self, mock_youtubeDL):
        download_youtube("https://www.youtube.com/watch?v=CmwSf7rI2II")
        mock_youtubeDL.assert_called_once()


class TestGenerateTranscript(TestCase):
    @patch("video.utils.whisper")
    @patch("video.utils.os")
    @patch("video.utils.download_youtube")
    @patch("video.utils.MP4")
    def test_generate_transcript_from_url(
        self, mock_mp4, mock_download_youtube, mock_os, mock_whisper
    ):
        mock_os.path.isfile.return_value = True
        mock_whisper.load_model.return_value.transcribe.return_value = {
            "text": "Sample transcript"
        }
        mock_mp4.return_value.info.length = 10.1
        user = User.objects.create(
            email="test@example.com",
            password="test",
            expiration_date=datetime.date.today(),
        )
        task = Task.objects.create(
            userID=user,
            url="https://www.youtube.com/watch?v=CmwSf7rI2II",
            status="0",
            mode="transcript",
        )
        transcript = generate_transcript_from_url(task)

        self.assertEqual(transcript, "Sample transcript")


class TestProcessVideoIntegration(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            email="test@example.com",
            password="test",
            expiration_date=datetime.date.today(),
        )
        self.task = Task.objects.create(
            userID=self.user,
            url="https://www.youtube.com/watch?v=CmwSf7rI2II",
            status="0",
            mode="transcript",
        )

    def test_process_video(self):
        process_video(self.task)

        self.assertEqual(self.task.status, "1")
        self.assertTrue(Video.objects.filter(taskID=self.task).exists())
        self.assertTrue(Transcript.objects.filter(taskID=self.task).exists())
