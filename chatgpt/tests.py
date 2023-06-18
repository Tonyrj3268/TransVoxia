from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
import json
from unittest.mock import patch

from .views import generate_text


class GenerateTextTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("chatgpt")  # 假定你的 ChatViewSet 對應的 url pattern 名稱為 'chat'

    @patch("chatgpt.views.generate_text")
    def test_generate_text_success(self, mock_generate_text):
        mock_generate_text.return_value = "Hello, world!"

        data = {
            "prompt": "Tell me a joke.",
        }
        response = self.client.post(
            self.url, data=json.dumps(data), content_type="application/json"
        )
        print(response)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue("response" in response.json())
        self.assertEqual(response.json()["response"], "Hello, world!")

    @patch("chatgpt.views.generate_text")
    def test_generate_text_failure(self, mock_generate_text):
        mock_generate_text.side_effect = Exception("API Error")  # 模擬函數拋出異常

        data = {
            "prompt": "Hello, world!",
        }
        response = self.client.post(
            self.url, data=json.dumps(data), content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertTrue("error" in response.json())
        self.assertEqual(response.json()["error"], "API Error")

    def test_bad_request(self):
        data = {
            # 沒有提供 'prompt' key 應該返回 400 錯誤
        }
        response = self.client.post(
            self.url, data=json.dumps(data), content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
