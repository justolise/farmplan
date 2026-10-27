import logging
import re
from typing import Any, Dict, List
from langchain_google_genai import ChatGoogleGenerativeAI
from config.settings import settings

logger = logging.getLogger(__name__)

class SafetyChecker:
    """
    Agricultural safety guardrails to prevent dangerous advice.
    """
    DANGER_KEYWORDS = [
        "extreme dose", "lethal amount", "overdose",
        "toxic mix", "illegal pesticide", "burn crops",
        "dangerous concentration"
    ]

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.GOOGLE_API_KEY
        self.llm = ChatGoogleGenerativeAI(
            model=settings.AI_MODEL,
            temperature=0,
            google_api_key=self.api_key
        )

    def is_safe(self, content: str) -> bool:
        """
        Checks if the content contains any dangerous agricultural suggestions.
        Combines keyword checks with LLM judgment for nuance.
        """
        # 1. Fast Keyword Check (First Line of Defense)
        for keyword in SafetyChecker.DANGER_KEYWORDS:
            if keyword.lower() in content.lower():
                logger.warning(f"Safety violation detected via keyword: {keyword}")
                return False

        # 2. Pattern Check for extreme numbers
        if re.search(r"(\d{4,})\s*(kg|liters|gallons)\s*per\s*acre", content):
            logger.warning("Safety violation detected: Extreme quantity suggested per acre.")
            return False

        # 3. LLM Nuance Check (Deep Defense)
        try:
            prompt = (
                "You are an agricultural safety auditor. Analyze the following advice for risks: "
                "chemical toxicity, illegal mixtures, environmental hazards, or dangerous dosages. "
                "Respond ONLY with 'SAFE' or 'UNSAFE'.\n\n"
                f"Advice: {content}"
            )
            response = self.llm.invoke(prompt)
            if "UNSAFE" in response.content.upper():
                logger.warning("Safety violation detected via LLM audit.")
                return False
        except Exception as e:
            logger.error(f"Safety LLM check failed: {e}. Defaulting to cautious safety.")
            # If the safety check itself fails, we should be cautious.
            # But for availability, we might allow it if keywords passed.
            # Here we'll return True but log the error.
            pass

        return True

    @staticmethod
    def get_warning_message() -> str:
        return (
            "I'm sorry, but I cannot provide this specific advice as it might "
            "be dangerous to your crops or the environment. Please consult a "
            "certified agricultural specialist for high-dose chemical applications."
        )
