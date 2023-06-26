from rest_framework import serializers
from audio.models import Play_ht_voices


# Create your serializers here.
class LanguageSerializer(serializers.ModelSerializer):
    language = serializers.ListField(child=serializers.CharField())

    class Meta:
        model = Play_ht_voices
        fields = ["language"]


class PlayHtVoicesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Play_ht_voices
        fields = ["voice", "voice_url"]
