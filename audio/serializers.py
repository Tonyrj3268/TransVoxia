from rest_framework import serializers
from audio.models import Play_ht_voices, LanguageMapping


# Create your serializers here.
class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = LanguageMapping
        fields = ["original_language", "mapped_language"]


class PlayHtVoicesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Play_ht_voices
        fields = ["voice", "voice_url"]
