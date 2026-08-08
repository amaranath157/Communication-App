from google import genai
from google.genai import types
import json
import re
import hashlib
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# ─── Greeting Detection (No API call — saves billing cost) ──────────────────
GREETING_PHRASES = {
    "hi", "hello", "hey", "hiya", "howdy", "greetings",
    "good morning", "good afternoon", "good evening", "good night",
    "good day", "what's up", "whats up", "sup", "yo",
    "how are you", "how are you doing", "how do you do",
    "nice to meet you", "pleased to meet you",
    "hi there", "hello there", "hey there",
}

GREETING_RESPONSES = [
    "Hey there! 👋 Great to see you practising English! Go ahead and type a sentence — I'll help you make it perfect.",
    "Hello! 😊 I'm your English coach. Write any sentence and I'll correct it and explain why!",
    "Hi! 👋 Ready to improve your English? Send me a sentence and let's get started!",
    "Hey! Great that you're here. Type something in English and I'll check it for you! 💬",
    "Good to see you! 😄 Let's practise — write a sentence and I'll give you feedback right away.",
]


def _is_greeting(text: str) -> bool:
    """Returns True if the entire input is just a greeting phrase."""
    cleaned = re.sub(r'[^\w\s]', '', text.strip().lower())
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned in GREETING_PHRASES


def _greeting_response(text: str) -> dict:
    """Returns a hardcoded friendly response — zero AI cost."""
    index = int(hashlib.md5(text.lower().strip().encode()).hexdigest(), 16) % len(GREETING_RESPONSES)
    return {
        "corrected_text": text,
        "detailed_feedback": GREETING_RESPONSES[index],
        "score_out_of_10": 10,
        "is_greeting": True,
    }


SYSTEM_PROMPT = (
    "You are a warm, natural English tutor. "
    "When given a text, follow this EXACT feedback format for 'detailed_feedback':\n\n"
    "FORMAT (if there are mistakes):\n"
    "[Encouraging opener like 'Nice try!' or 'Good effort!'] + [Corrected sentence] + [Short reason why, 1 sentence] + [Polished version if it sounds unnatural]\n\n"
    "FORMAT (if the text is already perfect):\n"
    "'Perfect! Go ahead!'\n\n"
    "RULES:\n"
    "- 'I go to school now' is WRONG → correct to 'I am going to school now' (present continuous for right now).\n"
    "- 'She go' → 'She goes' (third-person -s rule).\n"
    "- Always fix: wrong tense, missing capital 'I', missing period, unnatural phrasing.\n"
    "- Keep the full feedback under 3 sentences total.\n"
    "- Tone: warm and real, not robotic or over-the-top cheerful.\n\n"
    "EXAMPLE output for 'i go to school now':\n"
    "'Nice try! The correct sentence is: I am going to school now. "
    "Use am/is/are + verb-ing when talking about something happening right now. "
    "A more natural way to say it: I'm heading to school now.'\n\n"
    "Respond ONLY with valid JSON, no markdown, no code fences:\n"
    '{"corrected_text": string, "detailed_feedback": string, "score_out_of_10": integer}'
)


class GeminiService:
    """
    Evaluation service for AI Teacher using Google Gemini API.
    Reads GEMINI_API_KEY from Django settings (injected via .env or CI/CD secrets).
    """

    def __init__(self):
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if not api_key:
            logger.warning("GEMINI_API_KEY is not set in settings. The AI Teacher feature will not work.")
            self.client = None
        else:
            self.client = genai.Client(api_key=api_key)
            self.model_name = 'gemini-2.0-flash'

    def evaluate_text(self, text: str) -> dict:
        # ── Greeting short-circuit ───────────────────────────────────────────
        if _is_greeting(text):
            logger.info(f"[GeminiService] Greeting detected — skipping API: '{text}'")
            return _greeting_response(text)

        if not self.client:
            return {
                "corrected_text": text,
                "detailed_feedback": "AI Teacher is currently unavailable. Please configure a valid GEMINI_API_KEY.",
                "score_out_of_10": 0,
            }

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=f"{SYSTEM_PROMPT}\n\nHere is the learner's text to evaluate:\n{text}",
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=1000,
                ),
            )

            response_text = response.text.strip()

            # Strip markdown code fences if model wraps response
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            return json.loads(response_text.strip())

        except json.JSONDecodeError as e:
            logger.error(f"[GeminiService] JSON parse error: {e}")
            return {
                "corrected_text": text,
                "detailed_feedback": "Good try! I had a small issue parsing the response — please try again.",
                "score_out_of_10": 0,
            }
        except Exception as e:
            logger.error(f"[GeminiService] Error calling Gemini API: {e}")
            return {
                "corrected_text": text,
                "detailed_feedback": "Failed to process the text. Please try again later.",
                "score_out_of_10": 0,
            }
