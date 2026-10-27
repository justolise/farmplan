from typing import Any, Dict, List  # noqa: UP035

from agents.farm_agent import FarmPlanAgent
from services.farm_service import FarmService
from utils.helpers import convert_history_to_messages
from utils.memory_manager import MemoryManager


class ChatService:
    def __init__(self, api_key: str):
        self.agent = FarmPlanAgent(api_key=api_key)
        self.farm_service = FarmService()
        self.memory = MemoryManager()

    def process_message(self, history: List[Dict[str, Any]], user_input: str):
        # 1. Get contextual data
        profile = self.farm_service.get_full_profile()

        # 2. Manage Memory: Summarize old history and trim recent
        summary = self.memory.summarize_history(history)
        trimmed_history = self.memory.trim_history(history)

        # 3. Convert history for agent
        lc_messages = convert_history_to_messages(trimmed_history)

        # 4. Query Knowledge Base for context
        kb_context = self.agent.kb.query(user_input)

        # 5. Get agent response
        # Prepend summary to the context
        full_kb_context = f"Conversation Summary: {summary}\n\n{kb_context}" if summary else kb_context

        response_data = self.agent.get_response(
            messages=lc_messages,
            farm_profile=profile,
            kb_context=full_kb_context
        )

        return response_data

    def diagnose_image(self, image_bytes: bytes, prompt: str):
        return self.agent.analyze_image(image_bytes, prompt)
