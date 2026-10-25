import os
import re
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain.agents import AgentExecutor
from langchain.agents.agent import create_tool_calling_agent
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

        self.model_name = model_name or os.getenv("AI_MODEL", "gemini-1.5-flash")
        self.llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            temperature=0,
            google_api_key=self.api_key
        )
        self.parser = JsonOutputParser(pydantic_object=AgriResponse)
        self.kb = FarmKnowledgeBase(api_key=self.api_key)
        self.tools = [get_weather_forecast, get_market_prices, predict_crop_yield]
        self.agent_executor = self._create_executor()

    def _create_executor(self):
        # Try to use the agent creation function
        try:
            agent = create_tool_calling_agent(
                self.llm, 
                self.tools, 
                self.get_system_prompt()
            )
        except ImportError:
            # Fallback for older/different langchain versions
            from langchain.agents import create_openai_tools_agent
            agent = create_openai_tools_agent(
                self.llm, 
                self.tools, 
                self.get_system_prompt()
            )
            
        return AgentExecutor(agent=agent, tools=self.tools, verbose=False)

    def get_system_prompt(self):
        return (
            "You are an expert agricultural AI assistant. Use tools for weather, market, and yield predictions. "
            "Always provide actionable checklists. "
            f"Final answer MUST be JSON matching: {self.parser.get_format_instructions()}"
        )

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
        context = ""
        if farm_profile:
            context += f"Farm Profile: {farm_profile}\n"
        if kb_context:
            context += f"Technical Data from Documents:\n{kb_context}\n"

        history_text = "\n".join([f"{type(m).__name__}: {m.content}" for m in messages])
        final_input = f"{context}History:\n{history_text}\n"
        
        try:
            result = self.agent_executor.invoke({"input": final_input})
            return self._parse_output(result["output"])
        except Exception:
            return self._fallback_response("An error occurred during processing.")

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
