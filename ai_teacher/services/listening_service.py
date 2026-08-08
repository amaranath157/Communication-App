import json
import logging
from google import genai
from google.genai import types
from django.conf import settings

logger = logging.getLogger(__name__)

# ─── Sentence generation prompts by difficulty ────────────────────────────────
GENERATE_PROMPT = {
    "easy": (
        "Generate ONE simple English sentence suitable for a beginner learner. "
        "Use common everyday words, present tense, short (6–10 words). "
        "Respond with ONLY raw JSON, no markdown:\n"
        '{\"sentence\": \"<the sentence>\"}'
    ),
    "medium": (
        "Generate ONE natural English sentence at an intermediate level. "
        "It can include a variety of tenses and vocabulary (10–15 words). "
        "Respond with ONLY raw JSON, no markdown:\n"
        '{\"sentence\": \"<the sentence>\"}'
    ),
    "hard": (
        "Generate ONE advanced English sentence with rich vocabulary, idioms, or "
        "complex grammar (15–20 words). "
        "Respond with ONLY raw JSON, no markdown:\n"
        '{\"sentence\": \"<the sentence>\"}'
    ),
}

# ─── Evaluation prompt ────────────────────────────────────────────────────────
EVALUATE_PROMPT_TEMPLATE = """You are an English pronunciation and listening coach.

A learner was asked to REPEAT the following sentence exactly:
ORIGINAL: "{original}"

The learner said:
USER SAID: "{user_response}"

Compare them carefully. Evaluate how accurately the user repeated the sentence.

Rules:
- Minor spelling differences from speech-to-text are OK (e.g. "gonna" vs "going to")
- Missing or swapped words are errors
- Score 8–10 = good repetition, 0–7 = needs improvement
- If score < 8, write ONE short, specific tip about what the user missed or got wrong
- If score >= 8, set improvement to null

Respond ONLY with raw valid JSON, no markdown, no code fences:
{{"score_out_of_10": <integer 0-10>, "is_good": <true|false>, "improvement": <"one line tip" or null>}}"""


class ListeningService:
    """
    Uses Google Gemini API for:
    1. Generating English practice sentences
    2. Evaluating how accurately the user repeated the sentence
    """

    def __init__(self):
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if not api_key:
            logger.warning("GEMINI_API_KEY is not set. Listening feature will not work.")
            self.client = None
        else:
            self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.0-flash"

    def generate_sentence(self, difficulty: str = "medium") -> dict:
        """Generate a practice sentence at the given difficulty level."""
        if not self.client:
            return {
                "sentence": "The quick brown fox jumps over the lazy dog.",
                "error": True,
            }

        prompt = GENERATE_PROMPT.get(difficulty, GENERATE_PROMPT["medium"])

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.9,
                    max_output_tokens=100,
                ),
            )
            raw = response.text.strip()
            # Strip accidental markdown fences
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            if raw.endswith("```"):
                raw = raw[:-3]

            result = json.loads(raw.strip())
            result["error"] = False
            return result

        except json.JSONDecodeError as e:
            logger.error(f"[ListeningService] JSON parse error on generate: {e}")
            return {"sentence": "Practice makes perfect.", "error": True}
        except Exception as e:
            logger.error(f"[ListeningService] API error on generate: {e}")
            return {"sentence": "Practice makes perfect.", "error": True}

    def evaluate_response(self, original_sentence: str, user_response: str) -> dict:
        """Evaluate how accurately the user repeated the original sentence."""
        if not self.client:
            return {
                "score_out_of_10": 0,
                "is_good": False,
                "improvement": "AI service is unavailable — GEMINI_API_KEY not configured.",
                "error": True,
            }

        prompt = EVALUATE_PROMPT_TEMPLATE.format(
            original=original_sentence,
            user_response=user_response,
        )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=200,
                ),
            )
            raw = response.text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            if raw.endswith("```"):
                raw = raw[:-3]

            result = json.loads(raw.strip())
            result["error"] = False
            return result

        except json.JSONDecodeError as e:
            logger.error(f"[ListeningService] JSON parse error on evaluate: {e}")
            return {
                "score_out_of_10": 0,
                "is_good": False,
                "improvement": "Could not parse AI response. Please try again.",
                "error": True,
            }
        except Exception as e:
            logger.error(f"[ListeningService] API error on evaluate: {e}")
            return {
                "score_out_of_10": 0,
                "is_good": False,
                "improvement": f"Service error: {str(e)}",
                "error": True,
            }
