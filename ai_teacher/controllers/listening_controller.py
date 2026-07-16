import base64
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from asgiref.sync import async_to_sync
import edge_tts

from ai_teacher.serializers.listening_serializer import (
    ListeningGenerateRequestSerializer,
    ListeningEvaluateRequestSerializer,
)
from ai_teacher.services.listening_service import ListeningService

logger = logging.getLogger(__name__)


async def _text_to_speech_base64(text: str) -> str:
    """Convert text to speech using edge_tts and return base64-encoded audio."""
    communicate = edge_tts.Communicate(text, "en-US-JennyNeural")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return base64.b64encode(audio_data).decode("utf-8")


class ListeningGenerateView(APIView):
    """
    POST /api/v1/ai-teacher/listening/generate/

    Step 1 of the listening exercise:
    - AI generates a practice sentence at the requested difficulty level
    - TTS converts it to speech (base64 audio)
    - Frontend plays the audio and asks the user to repeat it
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Generate a listening practice sentence with TTS audio",
        operation_description=(
            "Generates an English sentence at the chosen difficulty level "
            "and returns it along with a base64-encoded MP3 audio for playback. "
            "Play the audio to the user, then collect their spoken response "
            "and send it to /listening/evaluate/."
        ),
        request_body=ListeningGenerateRequestSerializer,
        responses={
            200: openapi.Response(
                description="Sentence generated successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "data": {
                            "sentence": "She has been studying English for three years.",
                            "audio_base64": "<base64_mp3_string>",
                            "difficulty": "medium",
                        }
                    }
                }
            ),
            400: "Bad Request",
            401: "Unauthorized",
        },
        tags=["Listening Practice"],
    )
    def post(self, request):
        serializer = ListeningGenerateRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        difficulty = serializer.validated_data.get("difficulty", "medium")

        # Step 1: Generate sentence via AI
        service = ListeningService()
        gen_result = service.generate_sentence(difficulty=difficulty)
        sentence = gen_result.get("sentence", "Practice makes perfect.")

        # Step 2: Convert to speech
        audio_b64 = None
        try:
            audio_b64 = async_to_sync(_text_to_speech_base64)(sentence)
        except Exception as e:
            logger.error(f"[ListeningGenerateView] TTS error: {e}")

        return Response(
            {
                "success": True,
                "data": {
                    "sentence": sentence,
                    "audio_base64": audio_b64,
                    "difficulty": difficulty,
                },
            },
            status=status.HTTP_200_OK,
        )


class ListeningEvaluateView(APIView):
    """
    POST /api/v1/ai-teacher/listening/evaluate/

    Step 2 of the listening exercise:
    - Receives the original sentence and the user's repeated text (from STT)
    - AI evaluates accuracy of repetition
    - Returns score (0–10), pass/fail, and a single-line improvement tip if score < 8
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Evaluate how accurately the user repeated the sentence",
        operation_description=(
            "Send the original sentence (from /listening/generate/) and the user's "
            "speech-to-text transcript. Returns a score out of 10, whether it's good, "
            "and a one-line improvement tip if the score is below 8."
        ),
        request_body=ListeningEvaluateRequestSerializer,
        responses={
            200: openapi.Response(
                description="Evaluation successful",
                examples={
                    "application/json": {
                        "success": True,
                        "data": {
                            "score_out_of_10": 6,
                            "is_good": False,
                            "improvement": "You missed the word 'been' — the correct form is 'has been studying', not 'has studying'.",
                            "original_sentence": "She has been studying English for three years.",
                            "user_response": "She has studying English for three years.",
                        }
                    }
                }
            ),
            400: "Bad Request",
            401: "Unauthorized",
        },
        tags=["Listening Practice"],
    )
    def post(self, request):
        serializer = ListeningEvaluateRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        original_sentence = serializer.validated_data["original_sentence"]
        user_response = serializer.validated_data["user_response"]

        # Evaluate via AI
        service = ListeningService()
        result = service.evaluate_response(
            original_sentence=original_sentence,
            user_response=user_response,
        )

        return Response(
            {
                "success": not result.get("error", False),
                "data": {
                    "score_out_of_10": result.get("score_out_of_10", 0),
                    "is_good": result.get("is_good", False),
                    "improvement": result.get("improvement"),   # null if score >= 8
                    "original_sentence": original_sentence,
                    "user_response": user_response,
                },
            },
            status=status.HTTP_200_OK,
        )
