import sys
from agents.farm_agent import FarmPlanAgent

from langchain_core.messages import AIMessage, HumanMessage


def render_ui_response(data):
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

def main():
    try:
        agent = FarmPlanAgent()
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    messages = []
    print("Farmer AI Agent Initialized. Type 'exit' or 'quit' to stop.")
    
    while True:
        user_input = input("\nFarmer: ")
        if user_input.lower() in ['exit', 'quit']:
            break
        
        messages.append(HumanMessage(content=user_input))
        
        try:
            response_data = agent.get_response(messages)
            render_ui_response(response_data)
            # Store the response as a string for the LLM context
            messages.append(AIMessage(content=str(response_data)))
        except Exception as e:  # noqa: BLE001
            print(f"\nError: {e}")

if __name__ == "__main__":
    main()
