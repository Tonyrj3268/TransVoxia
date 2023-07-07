from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
import json
from unittest.mock import patch


class GenerateTextTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("chatgpt")  # 假定你的 ChatViewSet 對應的 url pattern 名稱為 'chat'

    @patch("chatgpt.utils.TextGenerator.generate_text")
    def test_generate_text_success(self, mock_generate_text):
        mock_generate_text.return_value = "Hello, world!"

        data = {
            "system_content": "You are a chatbot.",
            "user_content": "Tell me a joke",
        }
        response = self.client.post(
            self.url, data=json.dumps(data), content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue("response" in response.json())
        self.assertEqual(response.json()["response"], "Hello, world!")

    def test_generate_text_invalid_request(self):
        data = {}  # 提供无效的输入数据，缺少必需的字段
        response = self.client.post(
            self.url, data=json.dumps(data), content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("system_content" in response.json().keys())
        self.assertTrue("user_content" in response.json().keys())
        self.assertTrue(["This field is required."] in list(response.json().values()))

    @patch("chatgpt.utils.TextGenerator.generate_text")
    def test_generate_text_server_error(self, mock_generate_text):
        mock_generate_text.side_effect = Exception("API Error")

        data = {
            "system_content": "You are a chatbot.",
            "user_content": "Tell me a joke",
        }
        response = self.client.post(
            self.url, data=json.dumps(data), content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertTrue("error" in response.json())
