import os
import re
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain.agents import AgentExecutor
from schemas.agri_schema import AgriResponse
from tools.weather_tool import get_weather_forecast
from tools.market_tool import get_market_prices
from tools.yield_tool import predict_crop_yield
from agents.knowledge_base import FarmKnowledgeBase

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
        # In LangChain 0.2+, for tool-calling agents, we should use the tool-calling agent structure.
        # Since the legacy 'create_tool_calling_agent' is missing in the environment's namespace,
        # we use the modern approach: initializing the LLM with tools.
        
        llm_with_tools = self.llm.bind_tools(self.tools)
        
        # We create a simple manual agent loop if the standard helper is missing
        # but AgentExecutor still requires an agent. 
        # To avoid ImportError and maintain stability, we will use the 'create_openai_tools_agent' 
        # which is the standard for tool-calling in current versions.
        try:
            from langchain.agents import create_openai_tools_agent
            agent = create_openai_tools_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=self.get_system_prompt_as_chat_prompt()
            )
        except ImportError:
            # Final fallback: Use a simple prompt-based agent
            from langchain.agents import create_react_agent
            from langchain import hub
            prompt = hub.pull("hwchase17/react")
            agent = create_react_agent(self.llm, self.tools, prompt)

        return AgentExecutor(agent=agent, tools=self.tools, verbose=False)

    def get_system_prompt_as_chat_prompt(self):
        from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
        return ChatPromptTemplate.from_messages([
            ("system", "You are an expert agricultural AI assistant. Use tools for weather, market, and yield predictions. "
                       "Always provide actionable checklists. "
                       f"Final answer MUST be JSON matching: {self.parser.get_format_instructions()}"),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

    def get_system_prompt(self):
        # Kept for compatibility
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

        # Convert BaseMessages to a format AgentExecutor expects for 'messages' variable
        history = []
        for m in messages:
            role = "user" if isinstance(m, HumanMessage) else "assistant"
            history.append({"role": role, "content": m.content})

        final_input = f"{context}User Question: {messages[-1].content if messages else ''}"
        
        try:
            result = self.agent_executor.invoke({
                "input": final_input,
                "messages": history
            })
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
