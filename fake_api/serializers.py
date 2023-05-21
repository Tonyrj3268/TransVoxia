from rest_framework import serializers

from .models import Task


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        exclude = ("taskID", "userID")

    def to_representation(self, instance):
        # 獲取序列化的原始資料
        data = super().to_representation(instance)

        return data
