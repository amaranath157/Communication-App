from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from ai_teacher.serializers.teacher_serializer import EvaluationRequestSerializer
from ai_teacher.services.gemini_service import GeminiService
from asgiref.sync import async_to_sync
import edge_tts
import base64

async def get_tts_base64(text: str) -> str:
    communicate = edge_tts.Communicate(text, "en-US-JennyNeural")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return base64.b64encode(audio_data).decode('utf-8')

class EvaluateTextView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=EvaluationRequestSerializer,
        responses={
            200: openapi.Response(
                description="Evaluation successful",
                examples={
                    "application/json": {
                        "corrected_text": "I went to the market yesterday.",
                        "detailed_feedback": "Use the past tense 'went' instead of 'go' for completed actions.",
                        "score_out_of_10": 5
                    }
                }
            ),
            400: "Bad Request"
        }
    )
    def post(self, request):
        serializer = EvaluationRequestSerializer(data=request.data)
        if serializer.is_valid():
            text = serializer.validated_data['text']
            service = GeminiService()
            result = service.evaluate_text(text)
            
            # Extract spoken feedback
            spoken = result.get('detailed_feedback') or result.get('feedback') or result.get('response') or result.get('message') or result.get('result') or "I have finished evaluating."
            
            try:
                audio_b64 = async_to_sync(get_tts_base64)(spoken)
                result["audio_base64"] = audio_b64
            except Exception as e:
                print(f"TTS Error: {e}")
                
            return Response(result, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
