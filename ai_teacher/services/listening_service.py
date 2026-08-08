import json
import logging
from openai import OpenAI
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
    TEMPORARY: Uses GitHub Models (GPT-4o) for:
    1. Generating English practice sentences
    2. Evaluating how accurately the user repeated the sentence
    """

    def __init__(self):
        token = getattr(settings, 'GITHUB_MODELS_TOKEN', None)
        if not token:
            logger.warning("GH_MODELS_TOKEN is not set. Listening feature will not work.")
            self.client = None
        else:
            self.client = OpenAI(
                base_url="https://models.inference.ai.azure.com",
                api_key=token,
            )
        self.model = "gpt-4o"

    def generate_sentence(self, difficulty: str = "medium") -> dict:
        """Generate a practice sentence at the given difficulty level."""
        if not self.client:
            return {
                "sentence": "The quick brown fox jumps over the lazy dog.",
                "error": True,
            }

        prompt = GENERATE_PROMPT.get(difficulty, GENERATE_PROMPT["medium"])

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9,
                max_tokens=100,
            )
            raw = response.choices[0].message.content.strip()
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
                "improvement": "AI service is unavailable — GH_MODELS_TOKEN not configured.",
                "error": True,
            }

        prompt = EVALUATE_PROMPT_TEMPLATE.format(
            original=original_sentence,
            user_response=user_response,
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=200,
            )
            raw = response.choices[0].message.content.strip()
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
