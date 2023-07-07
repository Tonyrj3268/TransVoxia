from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from .serializers import ChatSerializer
from .utils import TextGeneratorFactory
from .api_description import chat_view_set


class ChatViewSet(APIView):
    @swagger_auto_schema(
        operation_description=chat_view_set,
        request_body=ChatSerializer,
        responses={200: ChatSerializer, 400: "Invalid request.", 500: "Server error."},
    )
    def post(self, request):
        serializer = ChatSerializer(data=request.data)
        if serializer.is_valid():
            system_content = serializer.validated_data["system_content"]
            user_content = serializer.validated_data["user_content"]
            try:
                # user = request.user
                # is_pro_user = user.is_subscription_active()
                is_pro_user = False
                generator = TextGeneratorFactory.create(is_pro_user)
                generated_text = generator.generate_text(system_content, user_content)
            except Exception as e:
                return Response({"error": str(e)}, status=500)
            return Response(
                {
                    "system_content": system_content,
                    "user_content": user_content,
                    "response": generated_text,
                },
                status=200,
            )
        return Response(serializer.errors, status=400)
