# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from .serializers import LanguageSerializer, PlayHtVoicesSerializer
from .models import Play_ht_voices, LanguageMapping
from .api_description import VoicesListView_set


class LanguageListView(APIView):
    @swagger_auto_schema(
        operation_description="A list of distinct languages from Deepl",
        responses={
            200: "Available Language list"
        },  # You may define your custom schema for output here
    )
    def get(self, request):
        languages = LanguageMapping.objects.all()
        serializer = LanguageSerializer(languages, many=True)
        return Response(serializer.data)


class VoicesListView(APIView):
    @swagger_auto_schema(
        operation_description=VoicesListView_set,
        responses={
            200: "Available Voices dictionary with language as key and voices as value"
        },  # You may define your custom schema for output here
    )
    def get(self, request):
        data = {}
        for language_mapping in LanguageMapping.objects.all():
            language = language_mapping.original_language
            formal_name = language_mapping.mapped_language
            voices = Play_ht_voices.objects.filter(language_mapping=language)
            voices_data = PlayHtVoicesSerializer(voices, many=True).data
            data[language] = {
                "formal_name": formal_name,
                "usable_voices": [voice_data["voice"] for voice_data in voices_data],
            }
        return Response(data)
