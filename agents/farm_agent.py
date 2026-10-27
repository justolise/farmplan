import logging
import re
from typing import Any

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from agents.knowledge_base import FarmKnowledgeBase
from config.settings import settings
from schemas.agri_schema import AgriResponse
from tools.market_tool import get_market_prices
from tools.weather_tool import get_weather_forecast
from tools.yield_tool import predict_crop_yield
from tools.farm_data_tool import get_farm_profile, list_farm_fields, get_field_activity_logs, search_activity_logs
from utils.guardrails import SafetyChecker

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FarmPlanAgent:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.GOOGLE_API_KEY
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in settings or environment.")

        self.llm = ChatGoogleGenerativeAI(
            model=settings.AI_MODEL,
            temperature=settings.TEMPERATURE,
            google_api_key=self.api_key
        )
        self.parser = JsonOutputParser(pydantic_object=AgriResponse)
        self.kb = FarmKnowledgeBase(api_key=self.api_key)
        self.tools = [
            get_weather_forecast,
            get_market_prices,
            predict_crop_yield,
            get_farm_profile,
            list_farm_fields,
            get_field_activity_logs,
            search_activity_logs,
            get_field_trend_analysis
        ]

    def analyze_image(self, image_bytes: bytes, prompt: str):
        try:
            message = HumanMessage(
                content=[
                    {"type": "text", "text": f"Diagnose this agricultural issue: {prompt}. Provide a structured response in JSON matching the AgriResponse schema."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_bytes}"}},
                ]
            )
            response = self.llm.invoke([message])
            return self._parse_output(response.content)
        except Exception as e:  # noqa: BLE001
            logger.error(f"Image analysis error: {e}")
            return self._fallback_response(str(e))

    def get_response(self, messages: list[BaseMessage], farm_profile: dict[str, Any] | None = None, kb_context: str | None = None) -> dict[str, Any]:
        system_instructions = (
            "You are an expert agricultural AI assistant specializing in East African farming (Kenya, Uganda, Tanzania). "
            "You have access to tools for weather, market, yield predictions, and farm database queries. "
            "Always provide actionable checklists. "
            "\n\nREGIONAL CONTEXT (EAST AFRICA):\n"
            "1. CURRENCY & UNITS: Use KES (Kenyan Shillings) as default. Use kg and standard bags (e.g., 90kg for maize). "
            "2. CLIMATE: Be mindful of the Long Rains (March-May) and Short Rains (Oct-Dec). Warn users about the dry periods in between.\n"
            "3. CROP FOCUS: Prioritize intelligence on Maize, Coffee, Tea, Pyrethrum, and Horticultural crops common in the region.\n"
            "4. PEST ALERT: Be hypersensitive to Fall Armyworm, Coffee Berry Borer, and Banana Wilt. If these are mentioned or suspected, treat as high-priority alerts.\n"
            "\nDOMAIN-SPECIFIC RIGOR RULES:\n"
            "1. CROSS-TOOL VERIFICATION: If you suggest any chemical application, fertilization, or irrigation, "
            "you MUST call get_weather_forecast. If rain is predicted within 24-48 hours, you MUST adjust your "
            "advice to warn the user about runoff or recommend waiting.\n"
            "2. CONFIDENCE SCORING: You must assess the consistency of your data. If tool outputs conflict "
            "(e.g., logs say soil is moist but weather says 2 weeks of drought), lower your confidence_score "
            "and explicitly mention the conflict in the summary.\n"
            "3. SOURCE PRIORITY: Prioritize data in this order: Real-time Tools > Farmer's Logs > Knowledge Base.\n"
            f"\nYou MUST respond ONLY in JSON matching this schema: {self.parser.get_format_instructions()}"
        )

        context = ""
        if farm_profile:
            context += f"Farm Profile: {farm_profile}\n"
        if kb_context:
            context += f"Technical Data from Documents:\n{kb_context}\n"

        llm_with_tools = self.llm.bind_tools(self.tools)
        all_messages = [SystemMessage(content=system_instructions + "\n" + context)] + messages

        try:
            max_iterations = 5
            tool_call_history = set() # Track tool calls to prevent loops

            for i in range(max_iterations):
                logger.info(f"Iteration {i+1}/{max_iterations}")
                response = llm_with_tools.invoke(all_messages)

                if not response.tool_calls:
                    # No more tools needed, try to parse as final JSON response
                    final_output = self._parse_output(response.content)

                    # Self-Reflection Step for Accuracy
                    final_output = self._reflect_and_refine(final_output, all_messages)

                    # Safety Guardrail Check
                    safety_checker = SafetyChecker(api_key=self.api_key)
                    if not safety_checker.is_safe(str(final_output)):
                        return {
                            "summary": SafetyChecker.get_warning_message(),
                            "requirements": [],
                            "pro_tip": "Safety first! Please verify chemical dosages with a professional.",
                            "alerts": ["SAFETY WARNING: Potentially dangerous advice blocked."],
                            "confidence_score": 0.0,
                            "verification_status": "Blocked by Safety Guardrails"
                        }

                    return final_output

                # Execute all tool calls in the response
                all_messages.append(response)
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    args = tool_call["args"]
                    args_str = str(args)
                    call_id = f"{tool_name}:{args_str}"

                    if call_id in tool_call_history:
                        logger.warning(f"Duplicate tool call detected: {call_id}. Skipping to avoid loop.")
                        all_messages.append(ToolMessage(tool_call_id=tool_call["id"], content="Error: This tool call was already attempted with these arguments. Please try a different approach or provide the final answer."))
                        continue

                    tool_call_history.add(call_id)
                    selected_tool = next((t for t in self.tools if t.name == tool_name), None)
                    if selected_tool:
                        logger.info(f"Executing tool: {tool_name} with args {args_str}")
                        try:
                            tool_output = selected_tool.invoke(args)
                            all_messages.append(ToolMessage(tool_call_id=tool_call["id"], content=str(tool_output)))
                        except Exception as e:
                            error_msg = str(e)
                            logger.error(f"Tool {tool_name} failed: {error_msg}")

                            # Adaptive Retry Logic: Provide the LLM with a hint on how to recover
                            recovery_hint = (
                                f"Error executing tool {tool_name}: {error_msg}. "
                                "The tool failed. Please try: 1) Using different search terms, "
                                "2) Checking if the ID is correct, or 3) Using an alternative tool to find the same information."
                            )
                            all_messages.append(ToolMessage(tool_call_id=tool_call["id"], content=recovery_hint))
                    else:
                        all_messages.append(ToolMessage(tool_call_id=tool_call["id"], content=f"Tool {tool_name} not found."))

            # If we reach max iterations, try to parse whatever the last response was
            return self._parse_output(response.content)
        except Exception as e:
            logger.exception(f"Agent response error: {e}")  # noqa: TRY401
            return self._fallback_response(str(e))

    def _reflect_and_refine(self, output: dict[str, Any], history: list[BaseMessage]) -> dict[str, Any]:
        """
        Accuracy Layer: Checks if the response is supported by the tool outputs in the history.
        """
        try:
            reflection_prompt = (
                "You are an agricultural quality auditor. Review the following proposed response "
                "against the tool data collected in the conversation history. "
                "Check for: 1. Contradictions with tool data, 2. Missing critical data, 3. Hallucinations. "
                "If the response is accurate and supported, respond with 'VALID'. "
                "If not, provide a brief correction and the response with 'INVALID: <correction>'.\n\n"
                f"History: {history}\n\n"
                f"Proposed Response: {output}"
            )
            reflection = self.llm.invoke(reflection_prompt)
            if "VALID" in reflection.content.upper() and "INVALID" not in reflection.content.upper():
                return output

            logger.info(f"Reflection triggered correction: {reflection.content}")
            # If invalid, we let the LLM try to refine the JSON one last time
            refine_prompt = (
                f"Your previous response was flagged for inaccuracies: {reflection.content}. "
                f"Please refine the JSON response to be accurate based on the data. "
                f"Respond ONLY in JSON: {output}"
            )
            refined_response = self.llm.invoke(refine_prompt)
            return self._parse_output(refined_response.content)
        except Exception as e:
            logger.error(f"Reflection error: {e}")
            return output

    def _parse_output(self, content: str) -> dict[str, Any]:
        try:
            return self.parser.parse(content)
        except Exception:  # noqa: BLE001
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                try: return self.parser.parse(json_match.group())
                except: pass  # noqa: E722, S110
            return self._fallback_response(content)

    def _fallback_response(self, content: str) -> dict[str, Any]:
        return {
            "summary": "I have some advice, but couldn't format it perfectly:",
            "requirements": [{"category": "General", "detail": content}],
            "pro_tip": "Check back soon for more structured insights.",
            "alerts": []
        }
