import json
import re
import hashlib
import logging
from openai import OpenAI
from django.conf import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a warm, natural English tutor. Never sound like a robot.

When you get a text, produce feedback in this EXACT structure inside "overall_feedback":

IF the text has mistakes:
  [Encouraging opener] + [Say the corrected sentence] + [One sentence explaining why] + [Polished version if the sentence sounds unnatural even after correction]

IF the text is already perfectly correct:
  "Perfect! Go ahead!"

STRICT RULES:
- "i go to school now" → corrected_text = "I am going to school now." — present continuous for actions happening right now.
- "She go" → "She goes" — third-person singular always adds -s.
- Fix everything: wrong tense, missing capital I, missing period, unnatural word choice.
- For each correction entry, explanation = ONE casual sentence max.
- overall_feedback tone: warm, honest, short. No fake praise like "Wonderful!" or "Great job!" unless truly perfect.
- Score honestly. A sentence with tense errors is not 9/10.

EXAMPLE — input: "i go to school now"
overall_feedback → "Nice try! Say: I am going to school now. Use 'am/is/are + verb-ing' when something is happening right now — that's called present continuous. A more natural way: I'm heading to school now."

EXAMPLE — input: "I am going to school now."
overall_feedback → "Perfect! Go ahead!"

Respond ONLY with raw valid JSON — no markdown, no code fences:

{
  "original_text": "<unchanged input>",
  "corrected_text": "<every error fixed>",
  "polished_version": "<how a native speaker would say it naturally, or same as corrected_text if already natural>",
  "corrections": [
    {
      "original": "<wrong word or phrase>",
      "correction": "<the right version>",
      "explanation": "<one casual sentence: why this is wrong>"
    }
  ],
  "overall_feedback": "<encouraging opener + corrected sentence + why + polished if needed — OR 'Perfect! Go ahead!'>",
  "score_out_of_10": <integer 1-10>
}
"""

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
        "original_text": text,
        "corrected_text": text,
        "polished_version": text,
        "corrections": [],
        "overall_feedback": GREETING_RESPONSES[index],
        "score_out_of_10": 10,
        "error": False,
        "is_greeting": True,
    }


class GitHubModelService:
    """
    Uses GitHub Models (GPT-4o) via the OpenAI-compatible endpoint.
    GitHub Models endpoint: https://models.inference.ai.azure.com
    """

    def __init__(self):
        token = getattr(settings, 'GITHUB_MODELS_TOKEN', None)
        if not token:
            logger.warning("GH_MODELS_TOKEN is not set. English coach feature will not work.")
            self.client = None
        else:
            self.client = OpenAI(
                base_url="https://models.inference.ai.azure.com",
                api_key=token,
            )
        self.model = "gpt-4o"

    def correct_english(self, text: str) -> dict:
        """
        Accepts raw English text and returns a structured correction response.
        Greetings are short-circuited locally — no API call, no billing.
        """
        # ── Greeting short-circuit ───────────────────────────────────────────
        if _is_greeting(text):
            logger.info(f"[GitHubModelService] Greeting detected — skipping API: '{text}'")
            return _greeting_response(text)

        if not self.client:
            return {
                "original_text": text,
                "corrected_text": text,
                "polished_version": text,
                "corrections": [],
                "overall_feedback": "AI English Coach is unavailable — GH_MODELS_TOKEN not configured.",
                "score_out_of_10": 0,
                "error": True,
            }

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": f"Please correct and polish this text:\n\n{text}"},
                ],
                temperature=0.3,
                max_tokens=1500,
            )

            raw = response.choices[0].message.content.strip()

            # Strip accidental markdown code fences if model adds them
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            if raw.endswith("```"):
                raw = raw[:-3]

            result = json.loads(raw.strip())
            result["error"] = False
            result["is_greeting"] = False
            return result

        except json.JSONDecodeError as e:
            logger.error(f"[GitHubModelService] JSON parse error: {e}")
            return {
                "original_text": text,
                "corrected_text": text,
                "polished_version": text,
                "corrections": [],
                "overall_feedback": "Could not parse AI response. Please try again.",
                "score_out_of_10": 0,
                "error": True,
            }
        except Exception as e:
            logger.error(f"[GitHubModelService] API error: {e}")
            return {
                "original_text": text,
                "corrected_text": text,
                "polished_version": text,
                "corrections": [],
                "overall_feedback": f"Service error: {str(e)}",
                "score_out_of_10": 0,
                "error": True,
            }
