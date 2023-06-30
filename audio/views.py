# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from .serializers import LanguageSerializer, PlayHtVoicesSerializer
from .models import Play_ht_voices


class LanguageListView(APIView):
    @swagger_auto_schema(
        operation_description="A list of distinct languages from Deepl",
        responses={
            200: "Available Language list"
        },  # You may define your custom schema for output here
    )
    def get(self, request):
        languages = Play_ht_voices.objects.values_list("language", flat=True).distinct()
        serializer = LanguageSerializer({"language": languages})
        return Response(serializer.data["language"])


class VoicesListView(APIView):
    @swagger_auto_schema(
        operation_description="A dictionary where the key is a language, and the value is a list of voices for that language from Play.ht",
        responses={
            200: "Available Voices dictionary with language as key and voices as value"
        },  # You may define your custom schema for output here
    )
    def get(self, request):
        data = {}
        for language in Play_ht_voices.objects.values_list(
            "language", flat=True
        ).distinct():
            voices = Play_ht_voices.objects.filter(language=language)
            data[language] = PlayHtVoicesSerializer(voices, many=True).data
        return Response(data)
