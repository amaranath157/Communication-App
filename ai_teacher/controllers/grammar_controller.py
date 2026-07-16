from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ai_teacher.serializers.grammar_serializer import (
    EnglishCorrectionRequestSerializer,
    EnglishCorrectionResponseSerializer,
)
from ai_teacher.services.github_service import GitHubModelService


class EnglishCorrectionView(APIView):
    """
    POST /api/v1/ai-teacher/correct/

    Accepts English text and returns:
    - corrected_text    : all grammar/spelling/punctuation errors fixed
    - polished_version  : concise, professional rewrite
    - corrections       : list of {original, correction, explanation}
    - overall_feedback  : summary of the learner's main weaknesses
    - score_out_of_10   : quality score
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Correct & polish English text",
        operation_description=(
            "Submit any English text. The AI will fix all grammar mistakes, "
            "provide a polished version, and explain each correction clearly."
        ),
        request_body=EnglishCorrectionRequestSerializer,
        responses={
            200: openapi.Response(
                description="Correction successful",
                examples={
                    "application/json": {
                        "original_text": "i go to market yesterday and buyed many thing",
                        "corrected_text": "I went to the market yesterday and bought many things.",
                        "polished_version": "Yesterday, I visited the market and purchased several items.",
                        "corrections": [
                            {
                                "original": "i",
                                "correction": "I",
                                "explanation": "The pronoun 'I' is always capitalised in English."
                            },
                            {
                                "original": "go",
                                "correction": "went",
                                "explanation": "'Went' is the past tense of 'go'. Use past tense for completed actions."
                            },
                            {
                                "original": "buyed",
                                "correction": "bought",
                                "explanation": "'Buy' is an irregular verb. Its past tense is 'bought', not 'buyed'."
                            },
                            {
                                "original": "many thing",
                                "correction": "many things",
                                "explanation": "'Thing' must be plural ('things') after 'many'."
                            }
                        ],
                        "overall_feedback": "Focus on irregular past tense verbs and noun pluralisation rules.",
                        "score_out_of_10": 4,
                        "error": False
                    }
                }
            ),
            400: "Bad Request — invalid or missing 'text' field",
            401: "Unauthorized — provide a valid Bearer token",
        },
        tags=["English Coach"],
    )
    def post(self, request):
        serializer = EnglishCorrectionRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        text = serializer.validated_data["text"]
        service = GitHubModelService()
        result = service.correct_english(text)

        return Response(
            {"success": not result.get("error", False), "data": result},
            status=status.HTTP_200_OK,
        )
