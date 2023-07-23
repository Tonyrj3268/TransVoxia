from rest_framework import serializers


class ChatSerializer(serializers.Serializer):
    max_length = 10000
    system_content = serializers.CharField(
        max_length=max_length, help_text="You are a talk show host in Taiwan."
    )
    user_content = serializers.CharField(
        max_length=max_length, help_text="I want to hear you tell a joke."
    )
    response = serializers.CharField(max_length=max_length, read_only=True)


class TranslatorChatgptSerializer(serializers.Serializer):
    max_length = 10000
    system_content = serializers.CharField(
        max_length=max_length, help_text="You are a talk show host in Taiwan."
    )
    user_content = serializers.CharField(
        max_length=max_length, help_text="I want to hear you tell a joke."
    )
    response = serializers.CharField(max_length=max_length, read_only=True)
