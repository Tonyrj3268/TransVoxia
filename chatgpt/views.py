from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from .serializers import ChatSerializer
from .utils import generate_text


class ChatViewSet(APIView):
    # use @swagger_auto_schema to customize this post function
    @swagger_auto_schema(
        operation_description="Generate a response to a prompt using GPT-3.5.",
        request_body=ChatSerializer,
        responses={200: ChatSerializer, 400: "Invalid request.", 500: "Server error."},
    )
    def post(self, request):
        serializer = ChatSerializer(data=request.data)
        if serializer.is_valid():
            prompt = serializer.validated_data["prompt"]
            try:
                response_text = generate_text(prompt)
            except Exception as e:
                return Response({"error": str(e)}, status=500)
            return Response({"prompt": prompt, "response": response_text}, status=200)
        return Response(serializer.errors, status=400)
