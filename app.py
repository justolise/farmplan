import streamlit as st
import json
import os
import base64
from datetime import datetime
from db.database import init_db, SessionLocal
from db.manager import FarmDataManager
from agents.farm_agent import FarmPlanAgent
from utils.helpers import convert_history_to_messages
from utils.notifications import notifier

init_db()

st.set_page_config(page_title="FarmPlan AI Pro", page_icon="🌾", layout="wide")

def apply_styles():
    st.markdown("""
        <style>
        /* Mobile Optimization */
        [data-testid="stSidebar"] { background-color: #f0f2f6; }
        .main { background-color: #fdfdfd; padding: 1rem; }
        
        /* Voice-like Input Simulation */
        .voice-btn {
            background-color: #2e7d32;
            color: white;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            float: right;
        }
        
        .pro-tip-container { background-color: #e8f5e9; border-left: 6px solid #2e7d32; padding: 20px; border-radius: 10px; margin-top: 15px; }
        .requirement-card { background-color: white; border: 1px solid #e0e0e0; padding: 12px; border-radius: 8px; margin-bottom: 10px; }
        .category-label { color: #2e7d32; font-weight: bold; text-transform: uppercase; font-size: 0.85em; margin-right: 10px; }
        .alert-banner { background-color: #ffebee; border: 1px solid #ef9a9a; color: #c62828; padding: 15px; border-radius: 10px; margin-bottom: 20px; font-weight: bold; text-align: center; }
        </style>
        """, unsafe_allow_html=True)

apply_styles()

db_session = SessionLocal()
manager = FarmDataManager(db_session)

with st.sidebar:
    st.title("🌾 FarmPlan Pro")
    st.subheader("🔑 API Config")
    api_key = st.text_input("Google API Key", type="password", value=st.secrets.get("GOOGLE_API_KEY", ""))
    openweather_key = st.text_input("OpenWeather API Key", type="password", value=st.secrets.get("OPENWEATHER_API_KEY", ""))
    model_choice = st.selectbox("AI Model", ["gemini-1.5-flash", "gemini-1.5-pro"], index=0)
    
    st.markdown("---")
    st.subheader("🚜 Farm Profile")
    profile = manager.get_profile()
    if not profile: profile = type('obj', (object,), {'location':'', 'soil_type':'', 'main_crops':'', 'size':''})
    loc = st.text_input("Location", value=getattr(profile, 'location', ''))
    soil = st.text_input("Soil Type", value=getattr(profile, 'soil_type', ''))
    crops = st.text_input("Main Crops", value=getattr(profile, 'main_crops', ''))
    size = st.text_input("Farm Size", value=getattr(profile, 'size', ''))
    if st.button("Save Profile"):
        manager.update_profile(loc, soil, crops, size)
        st.success("Profile Saved!")

    st.markdown("---")
    # Notifications panel in sidebar
    st.subheader("🔔 Notifications")
    alerts = notifier.get_all_notifications()
    if not alerts:
        st.write("No new alerts.")
    for a in alerts:
        st.markdown(f"**{a['timestamp']}**: {a['message']}")
    if st.button("Clear Alerts"):
        notifier.clear_notifications()
        st.rerun()

if openweather_key:
    os.environ["OPENWEATHER_API_KEY"] = openweather_key

@st.cache_resource
def init_agent(key, model):
    return FarmPlanAgent(api_key=key, model_name=model)

if not api_key:
    st.warning("Please enter your Google API Key.")
    st.stop()

agent = init_agent(api_key, model_choice)

# --- Navigation ---
page = st.selectbox("Navigate", ["AI Assistant", "Field Management", "Activity Log", "Knowledge Base", "Diagnosis", "Yield Analytics"])

if page == "AI Assistant":
    st.title("🤖 AI Assistant")
    
    # Voice Simulation Button
    st.markdown('<div class="voice-btn">🎙️</div>', unsafe_allow_html=True)
    st.caption("Voice input simulation active: Click mic to speak (Demo)")
    
    if "messages" not in st.session_state: st.session_state.messages = []
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                try:
                    data = json.loads(message["content"])
                    if data.get('alerts'):
                        for alert in data['alerts']: st.markdown(f'<div class="alert-banner">⚠️ {alert}</div>', unsafe_allow_html=True)
                    st.write(data.get('summary', ''))
                    cols = st.columns(2)
                    for idx, item in enumerate(data.get('requirements', [])):
                        with cols[idx % 2]: st.markdown(f'<div class="requirement-card"><span class="category-label">{item.get("category")}</span>{item.get("detail")}</div>', unsafe_allow_html=True)
                    if 'pro_tip' in data: st.markdown(f'<div class="pro-tip-container"><b>💡 Pro Tip:</b> {data["pro_tip"]}</div>', unsafe_allow_html=True)
                except: st.write(message["content"])
            else: st.write(message["content"])

    if prompt := st.chat_input("Ask me anything..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.write(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                p = manager.get_profile()
                profile_dict = {"location": getattr(p, 'location', ''), "soil": getattr(p, 'soil_type', ''), "crops": getattr(p, 'main_crops', ''), "size": getattr(p, 'size', '')}
                kb_context = agent.kb.query(prompt)
                res = agent.get_response(convert_history_to_messages(st.session_state.messages), farm_profile=profile_dict, kb_context=kb_context)
                
                # Trigger Notification if Agent returns alerts
                if res.get('alerts'):
                    for alert in res['alerts']: notifier.send_alert(alert, "HIGH")
                
                if res.get('alerts'):
                    for alert in res['alerts']: st.markdown(f'<div class="alert-banner">⚠️ {alert}</div>', unsafe_allow_html=True)
                st.write(res.get('summary', ''))
                cols = st.columns(2)
                for idx, item in enumerate(res.get('requirements', [])):
                    with cols[idx % 2]: st.markdown(f'<div class="requirement-card"><span class="category-label">{item.get("category")}</span>{item.get("detail")}</div>', unsafe_allow_html=True)
                if 'pro_tip' in res: st.markdown(f'<div class="pro-tip-container"><b>💡 Pro Tip:</b> {res["pro_tip"]}</div>', unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": json.dumps(res)})

elif page == "Field Management":
    st.title("🚜 Field Management")
    with st.expander("➕ Add New Field"):
        with st.form("add_field"):
            f_name = st.text_input("Field Name")
            f_crop = st.text_input("Current Crop")
            f_date = st.date_input("Planted Date")
            f_area = st.number_input("Area (Acres)", min_value=0.1)
            f_notes = st.text_area("Notes")
            if st.form_submit_button("Create Field"):
                manager.add_field(f_name, f_crop, datetime.combine(f_date, datetime.min.time()), f_area, f_notes)
                st.success(f"Field {f_name} created!")
                st.rerun()
    st.markdown("---")
    fields = manager.get_all_fields()
    for f in fields:
        with st.container():
            col1, col2 = st.columns([3, 1])
            col1.markdown(f"### {f.name} ({f.crop})")
            col1.write(f"📅 Planted: {f.planted_date.strftime('%Y-%m-%d') if f.planted_date else 'N/A'} | 📏 Area: {f.area} acres")
            if col2.button("🗑️ Delete", key=f"del_{f.id}"):
                manager.delete_field(f.id)
                st.rerun()

elif page == "Activity Log":
    st.title("📝 Activity Log")
    fields = manager.get_all_fields()
    if not fields: st.warning("Please create a field first.")
    else:
        selected_field = st.selectbox("Select Field", fields, format_func=lambda f: f.name)
        with st.expander("➕ Log Activity"):
            with st.form("log_activity"):
                a_type = st.selectbox("Activity Type", ["Fertilization", "Irrigation", "Pest Control", "Harvest", "Other"])
                a_desc = st.text_area("Description")
                a_amount = st.text_input("Amount")
                if st.form_submit_button("Add Log"):
                    manager.add_log(selected_field.id, a_type, a_desc, a_amount)
                    st.success("Activity logged!")
                    st.rerun()
        st.markdown("---")
        logs = manager.get_logs_for_field(selected_field.id)
        for l in logs: st.markdown(f'<div class="requirement-card"><b>{l.date.strftime("%Y-%m-%d")}</b> | <span class="category-label">{l.activity_type}</span><br>{l.description} <br><small>Amount: {l.amount}</small></div>', unsafe_allow_html=True)

elif page == "Knowledge Base":
    st.title("📚 Knowledge Base")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    if uploaded_file:
        with open("temp.pdf", "wb") as f: f.write(uploaded_file.getvalue())
        with st.spinner("Indexing document..."):
            agent.kb.add_document("temp.pdf")
        st.success("Document indexed successfully!")
    if st.button("Clear Knowledge Base"):
        agent.kb.clear()
        st.success("Knowledge base cleared!")

elif page == "Diagnosis":
    st.title("📸 Visual Diagnosis")
    img_file = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"])
    if img_file:
        st.image(img_file, caption="Uploaded Image")
        prompt = st.text_input("What would you like to know about this image?")
        if st.button("Analyze Image"):
            with st.spinner("Analyzing..."):
                bytes_data = img_file.getvalue()
                b64_img = base64.b64encode(bytes_data).decode('utf-8')
                res = agent.analyze_image(b64_img, prompt)
                if res.get('alerts'):
                    for alert in res['alerts']: notifier.send_alert(alert, "HIGH")
                if res.get('alerts'):
                    for alert in res['alerts']: st.markdown(f'<div class="alert-banner">⚠️ {alert}</div>', unsafe_allow_html=True)
                st.write(res.get('summary', ''))
                cols = st.columns(2)
                for idx, item in enumerate(res.get('requirements', [])):
                    with cols[idx % 2]: st.markdown(f'<div class="requirement-card"><span class="category-label">{item.get("category")}</span>{item.get("detail")}</div>', unsafe_allow_html=True)
                if 'pro_tip' in res: st.markdown(f'<div class="pro-tip-container"><b>💡 Pro Tip:</b> {res["pro_tip"]}</div>', unsafe_allow_html=True)

elif page == "Yield Analytics":
    st.title("📈 Yield Analytics")
    fields = manager.get_all_fields()
    if not fields:
        st.warning("Create fields to see yield analytics.")
    else:
        selected_field = st.selectbox("Select Field", fields, format_func=lambda f: f.name)
        if st.button("Calculate Predicted Yield"):
            with st.spinner("Computing based on field history..."):
                # Calculate a mock health score based on logs
                logs = manager.get_logs_for_field(selected_field.id)
                health_score = 1.0 if len(logs) > 2 else 0.7
                prediction = agent.agent_executor.invoke({"input": f"Predict yield for {selected_field.crop} on {selected_field.area} acres with health score {health_score}"})
                st.success(prediction["output"])
