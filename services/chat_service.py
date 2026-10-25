import json
from typing import List, Dict, Any
from agents.farm_agent import FarmPlanAgent
from services.farm_service import FarmService
from utils.helpers import convert_history_to_messages
from config.settings import settings

class ChatService:
    def __init__(self, api_key: str):
        self.agent = FarmPlanAgent(api_key=api_key)
        self.farm_service = FarmService()

    def process_message(self, history: List[Dict[str, Any]], user_input: str):
        # 1. Get contextual data
        profile = self.farm_service.get_full_profile()
        
        # 2. Convert history for agent
        lc_messages = convert_history_to_messages(history)
        
        # 3. Query Knowledge Base for context
        kb_context = self.agent.kb.query(user_input)
        
        # 4. Get agent response
        response_data = self.agent.get_response(
            messages=lc_messages, 
            farm_profile=profile, 
            kb_context=kb_context
        )
        
        return response_data

    def diagnose_image(self, image_bytes: bytes, prompt: str):
        return self.agent.analyze_image(image_bytes, prompt)
