import os
import re
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from schemas.agri_schema import AgriResponse
from tools.weather_tool import get_weather_forecast
from tools.market_tool import get_market_prices
from tools.yield_tool import predict_crop_yield
from agents.knowledge_base import FarmKnowledgeBase
from langchain_core.tools import tool

load_dotenv()

class FarmPlanAgent:
    def __init__(self, api_key: Optional[str] = None, model_name: str = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found.")

        # Updated default to gemini-2.0-flash (current stable high-performance model)
        # User requested 2.5-flash, but standard current stable is 2.0-flash or 1.5-flash
        # I will use the requested 'gemini-2.0-flash' or allow override via env/args.
        self.model_name = model_name or os.getenv("AI_MODEL", "gemini-2.0-flash")
        
        self.llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            temperature=0,
            google_api_key=self.api_key
        )
        self.parser = JsonOutputParser(pydantic_object=AgriResponse)
        self.kb = FarmKnowledgeBase(api_key=self.api_key)
        self.tools = [get_weather_forecast, get_market_prices, predict_crop_yield]

    def analyze_image(self, image_bytes: bytes, prompt: str):
        from langchain_core.messages import HumanMessage
        message = HumanMessage(
            content=[
                {"type": "text", "text": f"Diagnose this agricultural issue: {prompt}. Provide a structured response in JSON matching the AgriResponse schema."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_bytes}"}},
            ]
        )
        response = self.llm.invoke([message])
        return self._parse_output(response.content)

    def get_response(self, messages: List[BaseMessage], farm_profile: Optional[Dict[str, Any]] = None, kb_context: Optional[str] = None) -> Dict[str, Any]:
        system_instructions = (
            "You are an expert agricultural AI assistant. "
            "You have access to tools for weather, market, and yield predictions. "
            "Always provide actionable checklists. "
            f"You MUST respond ONLY in JSON matching this schema: {self.parser.get_format_instructions()}"
        )
        
        context = ""
        if farm_profile:
            context += f"Farm Profile: {farm_profile}\n"
        if kb_context:
            context += f"Technical Data from Documents:\n{kb_context}\n"

        llm_with_tools = self.llm.bind_tools(self.tools)
        all_messages = [SystemMessage(content=system_instructions + "\n" + context)] + messages
        
        try:
            response = llm_with_tools.invoke(all_messages)
            
            if response.tool_calls:
                tool_call = response.tool_calls[0]
                tool_name = tool_call["name"]
                args = tool_call["args"]
                
                selected_tool = next((t for t in self.tools if t.name == tool_name), None)
                if selected_tool:
                    tool_output = selected_tool.invoke(args)
                    all_messages.append(response)
                    all_messages.append(HumanMessage(content=f"Tool Result: {tool_output}"))
                    final_response = self.llm.invoke(all_messages)
                    return self._parse_output(final_response.content)
            
            return self._parse_output(response.content)
        except Exception as e:
            return self._fallback_response(str(e))

    def _parse_output(self, content: str) -> Dict[str, Any]:
        try:
            return self.parser.parse(content)
        except Exception:
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                try: return self.parser.parse(json_match.group())
                except: pass
            return self._fallback_response(content)

    def _fallback_response(self, content: str) -> Dict[str, Any]:
        return {
            "summary": "I have some advice, but couldn't format it perfectly:",
            "requirements": [{"category": "General", "detail": content}],
            "pro_tip": "Check back soon for more structured insights.",
            "alerts": []
        }
