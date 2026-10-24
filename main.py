import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

def render_ui_response(content):
    """Simulates a polished UI rendering of the JSON response."""
    try:
        data = json.loads(content)
        
        print("\n" + "="*50)
        print(f"✨ {data.get('summary', 'Agricultural Advice')}")
        print("="*50)
        
        for item in data.get('requirements', []):
            category = item.get('category', 'Detail')
            detail = item.get('detail', '')
            print(f"🔹 {category.upper()}: {detail}")
            
        if 'pro_tip' in data:
            print("\n" + "-"*50)
            print(f"💡 PRO TIP: {data['pro_tip']}")
            print("-"*50)
            
    except json.JSONDecodeError:
        print(f"\nAgent: {content}")

def main():
    # Using gemini-1.5-flash for faster responses and better JSON adherence
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    
    system_prompt = (
        "You are an expert agricultural AI assistant. "
        "You MUST respond ONLY in JSON format. "
        "The JSON should follow this structure: "
        "{"
        "  'summary': 'A friendly, human-readable introductory sentence.',"
        "  'requirements': ["
        "    {'category': 'e.g., Soil', 'detail': 'The specific advice'},"
        "    {'category': 'e.g., Water', 'detail': 'The specific advice'}"
        "  ],"
        "  'pro_tip': 'A highly actionable, gold-standard piece of advice.'"
        "}"
        "Avoid markdown code blocks in your response, just the raw JSON."
    )
    
    messages = [
        SystemMessage(content=system_prompt),
    ]
    
    print("Farmer AI Agent Initialized. Type 'exit' or 'quit' to stop.")
    
    while True:
        user_input = input("\nFarmer: ")
        if user_input.lower() in ['exit', 'quit']:
            break
        
        messages.append(HumanMessage(content=user_input))
        
        try:
            response = llm.invoke(messages)
            render_ui_response(response.content)
            messages.append(response)
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    main()
