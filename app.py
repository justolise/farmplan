import streamlit as st
import json
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

load_dotenv()

# Page Config
st.set_page_config(page_title="FarmPlan AI", page_icon="🌾", layout="centered")

# Custom CSS for a cleaner look
st.markdown("""
    <style>
    .stChatMessage {
        border-radius: 15px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .pro-tip {
        background-color: #f0f2f6;
        border-left: 5px solid #2e7d32;
        padding: 15px;
        border-radius: 5px;
        font-style: italic;
        margin-top: 10px;
    }
    .category-header {
        font-weight: bold;
        color: #2e7d32;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize AI
def get_ai_response(messages):
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)
    
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
    
    # Prepend system message to the conversation
    full_messages = [SystemMessage(content=system_prompt)] + messages
    response = llm.invoke(full_messages)
    return response.content

# Session State for Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# UI Header
st.title("🌾 FarmPlan AI")
st.markdown("Your expert companion for sustainable and high-yield farming.")

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            try:
                data = json.loads(message["content"])
                st.write(data.get('summary', ''))
                
                for item in data.get('requirements', []):
                    st.markdown(f"**{item.get('category', '')}**: {item.get('detail', '')}")
                
                if 'pro_tip' in data:
                    st.markdown(f'<div class="pro-tip">💡 <b>Pro Tip:</b> {data["pro_tip"]}</div>', unsafe_allow_html=True)
            except:
                st.write(message["content"])
        else:
            st.write(message["content"])

# User Input
if prompt := st.chat_input("How can I help your farm today?"):
    # Add user message to state
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Generate AI response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing agricultural data..."):
            # Convert session state to LangChain messages
            lc_messages = []
            for m in st.session_state.messages:
                if m["role"] == "user":
                    lc_messages.append(HumanMessage(content=m["content"]))
                elif m["role"] == "assistant":
                    lc_messages.append(AIMessage(content=m["content"]))
            
            response_content = get_ai_response(lc_messages)
            
            # Render response
            try:
                data = json.loads(response_content)
                st.write(data.get('summary', ''))
                for item in data.get('requirements', []):
                    st.markdown(f"**{item.get('category', '')}**: {item.get('detail', '')}")
                if 'pro_tip' in data:
                    st.markdown(f'<div class="pro-tip">💡 <b>Pro Tip:</b> {data["pro_tip"]}</div>', unsafe_allow_html=True)
            except:
                st.write(response_content)
                
    # Save AI response to state
    st.session_state.messages.append({"role": "assistant", "content": response_content})
