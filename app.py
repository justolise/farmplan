import base64
import json
import os
from datetime import datetime

import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI

from config.settings import settings
from db.database import SessionLocal, init_db
from services.chat_service import ChatService
from services.farm_service import FarmService
from utils.notifications import notifier

init_db()

st.set_page_config(page_title=settings.APP_NAME, page_icon="🌾", layout="wide")


def apply_styles():
    st.markdown(
        """
        <style>
        .main { background-color: #fdfdfd; padding: 1rem; }
        .pro-tip-container { background-color: #e8f5e9; border-left: 6px solid #2e7d32; padding: 20px; border-radius: 10px; margin-top: 15px; }
        .requirement-card { background-color: white; border: 1px solid #e0e0e0; padding: 12px; border-radius: 8px; margin-bottom: 10px; }
        .category-label { color: #2e7d32; font-weight: bold; text-transform: uppercase; font-size: 0.85em; margin-right: 10px; }
        .alert-banner { background-color: #ffebee; border: 1px solid #ef9a9a; color: #c62828; padding: 15px; border-radius: 10px; margin-bottom: 20px; font-weight: bold; text-align: center; }
        </style>
        """,
        unsafe_allow_html=True,
    )


apply_styles()

# Initialize Services
db_session = SessionLocal()
farm_service = FarmService(db=db_session)

with st.sidebar:
    st.title(f"🌾 {settings.APP_NAME}")
    st.subheader("🔑 API Config")
    api_key = st.text_input(
        "Google API Key", type="password", value=st.secrets.get("GOOGLE_API_KEY", "")
    )
    openweather_key = st.text_input(
        "OpenWeather API Key",
        type="password",
        value=st.secrets.get("OPENWEATHER_API_KEY", ""),
    )
    model_choice = st.selectbox(
        "AI Model", ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash"], index=2
    )

    st.markdown("---")
    st.subheader("🚜 Farm Profile")
    profile = farm_service.get_full_profile()
    loc = st.text_input("Location", value=profile["location"])
    soil = st.text_input("Soil Type", value=profile["soil"])
    crops = st.text_input("Main Crops", value=profile["crops"])
    size = st.text_input("Farm Size", value=profile["size"])
    if st.button("Save Profile"):
        farm_service.update_farm_profile(
            {"location": loc, "soil": soil, "crops": crops, "size": size}
        )
        st.success("Profile Saved!")

    st.markdown("---")
    st.subheader("🔔 Notifications")

    # Notification channel selection
    channels = ["console", "whatsapp", "sms"]
    selected_channels = st.multiselect(
        "Active Channels",
        channels,
        default=["console"]
    )

    if st.button("Update Channels"):
        # Reset active providers
        notifier.active_providers = selected_channels
        st.success("Notification channels updated!")

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

# Initialize Chat Service
if not api_key:
    st.warning("Please enter your Google API Key.")
    st.stop()

chat_service = ChatService(api_key=api_key)
# Update agent model based on selection
chat_service.agent.model_name = model_choice
chat_service.agent.llm = ChatGoogleGenerativeAI(
    model=model_choice, temperature=settings.TEMPERATURE, google_api_key=api_key
)

page = st.selectbox(
    "Navigate",
    [
        "AI Assistant",
        "Field Management",
        "Activity Log",
        "Knowledge Base",
        "Diagnosis",
        "Yield Analytics",
    ],
)

if page == "AI Assistant":
    st.title("🤖 AI Assistant")
    if "messages" not in st.session_state:
        st.session_state.messages = []
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                try:
                    data = json.loads(message["content"])
                    if data.get("alerts"):
                        for alert in data["alerts"]:
                            st.markdown(
                                f'<div class="alert-banner">⚠️ {alert}</div>',
                                unsafe_allow_html=True,
                            )
                    st.write(data.get("summary", ""))
                    cols = st.columns(2)
                    for idx, item in enumerate(data.get("requirements", [])):
                        with cols[idx % 2]:
                            st.markdown(
                                f'<div class="requirement-card"><span class="category-label">{item.get("category")}</span>{item.get("detail")}</div>',
                                unsafe_allow_html=True,
                            )
                    if "pro_tip" in data:
                        st.markdown(
                            f'<div class="pro-tip-container"><b>💡 Pro Tip:</b> {data["pro_tip"]}</div>',
                            unsafe_allow_html=True,
                        )
                except:  # noqa: E722
                    st.write(message["content"])
            else:
                st.write(message["content"])

    if prompt := st.chat_input("Ask me anything..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        with st.chat_message("assistant"), st.spinner("Analyzing..."):
                res = chat_service.process_message(st.session_state.messages, prompt)
                if res.get("alerts"):
                    for alert in res["alerts"]:
                        notifier.send_alert(alert, "HIGH")
                if res.get("alerts"):
                    for alert in res["alerts"]:
                        st.markdown(
                            f'<div class="alert-banner">⚠️ {alert}</div>',
                            unsafe_allow_html=True,
                        )
                st.write(res.get("summary", ""))
                cols = st.columns(2)
                for idx, item in enumerate(res.get("requirements", [])):
                    with cols[idx % 2]:
                        st.markdown(
                            f'<div class="requirement-card"><span class="category-label">{item.get("category")}</span>{item.get("detail")}</div>',
                            unsafe_allow_html=True,
                        )
                if "pro_tip" in res:
                    st.markdown(
                        f'<div class="pro-tip-container"><b>💡 Pro Tip:</b> {res["pro_tip"]}</div>',
                        unsafe_allow_html=True,
                    )
                st.session_state.messages.append(
                    {"role": "assistant", "content": json.dumps(res)}
                )

elif page == "Field Management":
    st.title("🚜 Field Management")
    with st.expander("➕ Add New Field"), st.form("add_field"):
        f_name = st.text_input("Field Name")
        f_crop = st.text_input("Current Crop")
        f_date = st.date_input("Planted Date")
        f_area = st.number_input("Area (Acres)", min_value=0.1)
        f_notes = st.text_area("Notes")
        if st.form_submit_button("Create Field"):
            farm_service.manage_fields(
                "add",
                {
                    "name": f_name,
                    "crop": f_crop,
                    "date": datetime.combine(f_date, datetime.min.time()),
                    "area": f_area,
                    "notes": f_notes,
                },
            )
            st.success(f"Field {f_name} created!")
            st.rerun()
    st.markdown("---")
    fields = farm_service.manage_fields("list")
    for f in fields:
        with st.container():
            col1, col2 = st.columns([3, 1])
            col1.markdown(f"### {f.name} ({f.crop})")
            col1.write(
                f"📅 Planted: {f.planted_date.strftime('%Y-%m-%d') if f.planted_date else 'N/A'} | 📏 Area: {f.area} acres"
            )
            if col2.button("🗑️ Delete", key=f"del_{f.id}"):
                farm_service.manage_fields("delete", field_id=f.id)
                st.rerun()

elif page == "Activity Log":
    st.title("📝 Activity Log")
    fields = farm_service.manage_fields("list")
    if not fields:
        st.warning("Please create a field first.")
    else:
        selected_field = st.selectbox(
            "Select Field", fields, format_func=lambda f: f.name
        )
        with st.expander("➕ Log Activity"):  # noqa: SIM117
            with st.form("log_activity"):
                a_type = st.selectbox(
                    "Activity Type",
                    ["Fertilization", "Irrigation", "Pest Control", "Harvest", "Other"],
                )
                a_desc = st.text_area("Description")
                a_amount = st.text_input("Amount")
                if st.form_submit_button("Add Log"):
                    farm_service.log_activity(
                        selected_field.id,
                        {"type": a_type, "description": a_desc, "amount": a_amount},
                    )
                    st.success("Activity logged!")
                    st.rerun()
        st.markdown("---")
        logs = farm_service.get_field_logs(selected_field.id)
        for l in logs:
            st.markdown(
                f'<div class="requirement-card"><b>{l.date.strftime("%Y-%m-%d")}</b> | <span class="category-label">{l.activity_type}</span><br>{l.description} <br><small>Amount: {l.amount}</small></div>',
                unsafe_allow_html=True,
            )

elif page == "Knowledge Base":
    st.title("📚 Knowledge Base")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    if uploaded_file:
        with open("temp.pdf", "wb") as f:
            f.write(uploaded_file.getvalue())
        with st.spinner("Indexing document..."):
            chat_service.agent.kb.add_document("temp.pdf")
        st.success("Document indexed successfully!")
    if st.button("Clear Knowledge Base"):
        chat_service.agent.kb.clear()
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
                b64_img = base64.b64encode(bytes_data).decode("utf-8")
                res = chat_service.diagnose_image(b64_img, prompt)
                if res.get("alerts"):
                    for alert in res["alerts"]:
                        notifier.send_alert(alert, "HIGH")
                if res.get("alerts"):
                    for alert in res["alerts"]:
                        st.markdown(
                            f'<div class="alert-banner">⚠️ {alert}</div>',
                            unsafe_allow_html=True,
                        )
                st.write(res.get("summary", ""))
                cols = st.columns(2)
                for idx, item in enumerate(res.get("requirements", [])):
                    with cols[idx % 2]:
                        st.markdown(
                            f'<div class="requirement-card"><span class="category-label">{item.get("category")}</span>{item.get("detail")}</div>',
                            unsafe_allow_html=True,
                        )
                if "pro_tip" in res:
                    st.markdown(
                        f'<div class="pro-tip-container"><b>💡 Pro Tip:</b> {res["pro_tip"]}</div>',
                        unsafe_allow_html=True,
                    )

elif page == "Yield Analytics":
    st.title("📈 Yield Analytics")
    fields = farm_service.manage_fields("list")
    if not fields:
        st.warning("Create fields to see yield analytics.")
    else:
        selected_field = st.selectbox(
            "Select Field", fields, format_func=lambda f: f.name
        )
        if st.button("Calculate Predicted Yield"):
            with st.spinner("Computing..."):
                logs = farm_service.get_field_logs(selected_field.id)
                health_score = 1.0 if len(logs) > 2 else 0.7
                # Need to query the agent to get the prediction
                res = chat_service.process_message(
                    [],
                    f"Predict yield for {selected_field.crop} on {selected_field.area} acres with health score {health_score}",
                )
                st.write(res.get("summary", ""))
                if "pro_tip" in res:
                    st.markdown(
                        f'<div class="pro-tip-container"><b>💡 Pro Tip:</b> {res["pro_tip"]}</div>',
                        unsafe_allow_html=True,
                    )
