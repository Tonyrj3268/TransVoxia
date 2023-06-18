from rest_framework import serializers


class ChatSerializer(serializers.Serializer):
    max_length = 200
    prompt = serializers.CharField(max_length=max_length)
    response = serializers.CharField(max_length=max_length, read_only=True)
