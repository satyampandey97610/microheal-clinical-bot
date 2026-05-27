"""
MicroHeal Clinical Bot — Streamlit UI
======================================
This is the frontend. All intelligence lives in clinical_engine.py.
"""

import streamlit as st
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
if Path(".env").exists():
    load_dotenv(dotenv_path=Path(__file__).parent / ".env")

if "OPENAI_API_KEY" not in os.environ and "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

# Import the core engine
from clinical_engine import ClinicalEngine

# ──────────────────────────────────────────────────────────────────
#  Streamlit Page Config & CSS
# ──────────────────────────────────────────────────────────────────

st.set_page_config(page_title="MicroHeal Clinical Bot", page_icon="⚕️", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    .stApp { background-color: #fcfcfc !important; }
    html, body { font-family: 'Inter', sans-serif; color: #1e293b; }
    .stTitle { font-weight: 800 !important; font-size: 2.8rem !important; margin-bottom: 0px !important; }
    .specialty-badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.9rem; font-weight: 600; margin-bottom: 20px; }
    .badge-gastro { background-color: #dbeafe; color: #1e3a8a; }
    .badge-cardio { background-color: #fee2e2; color: #991b1b; }
    .badge-nephro { background-color: #ccfbf1; color: #115e59; }
    [data-testid="stChatMessage"] { border-radius: 12px !important; border: 1px solid #e2e8f0 !important; background: #ffffff !important; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 15px;}
    [data-testid="stChatMessage"]:nth-child(even) { background: #f8fafc !important; }
    .micro-ref { font-size: 0.85rem !important; color: #475569 !important; margin-bottom: 6px; padding: 6px; background: #f1f5f9; border-radius: 6px; border-left: 3px solid #3b82f6; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────
#  Sidebar
# ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3004/3004458.png", width=60)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ──────────────────────────────────────────────────────────────────
#  Model Selector (Gemini-style dropdown at the top)
# ──────────────────────────────────────────────────────────────────

col1, col2 = st.columns([1, 4])
with col1:
    selected_domain = st.selectbox(
        "Model Selector",
        ["Gastroenterology", "Cardiology", "Nephrology"],
        label_visibility="collapsed"
    )

# Map UI domain to engine key
domain_map = {
    "Gastroenterology": "gastro",
    "Cardiology": "cardio",
    "Nephrology": "nephro"
}
domain_key = domain_map[selected_domain]

# Initialize engine (cached)
@st.cache_resource
def get_engine(key):
    return ClinicalEngine(key)

engine = get_engine(domain_key)

# ──────────────────────────────────────────────────────────────────
#  State Isolation — clear chat when switching domains
# ──────────────────────────────────────────────────────────────────

if "current_domain" not in st.session_state:
    st.session_state.current_domain = selected_domain
    st.session_state.messages = []
elif st.session_state.current_domain != selected_domain:
    st.session_state.current_domain = selected_domain
    st.session_state.messages = []

# ──────────────────────────────────────────────────────────────────
#  Header
# ──────────────────────────────────────────────────────────────────

if selected_domain == "Gastroenterology":
    theme_color = "#3b82f6"
    icon = "🩺"
    badge_class = "badge-gastro"
elif selected_domain == "Cardiology":
    theme_color = "#ef4444"
    icon = "❤️"
    badge_class = "badge-cardio"
else:  # Nephrology
    theme_color = "#14b8a6"
    icon = "💧"
    badge_class = "badge-nephro"

st.markdown(f'<h1 class="stTitle" style="color: {theme_color};">MicroHeal Clinical Bot</h1>', unsafe_allow_html=True)
st.markdown(f'<div class="specialty-badge {badge_class}">{icon} {selected_domain} Expert</div>', unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────
#  Chat History
# ──────────────────────────────────────────────────────────────────

for msg in st.session_state.messages:
    avatar = "🩺" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"], unsafe_allow_html=True)
        if "sources" in msg and msg["sources"]:
            with st.expander("📚 View Evidence Citations"):
                for r in msg["sources"]:
                    st.markdown(f'<div class="micro-ref"><b>{r["type"].upper()}</b> | {r["source"]} — <i>{r["title"]}</i></div>', unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────
#  Chat Input — uses ClinicalEngine for ALL logic
# ──────────────────────────────────────────────────────────────────

if user_input := st.chat_input(f"Ask a {selected_domain.lower()} clinical question..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar="🩺"):
        with st.spinner(f"Searching {selected_domain} knowledge base..."):

            # Build history for context
            history = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages[:-1]
            ]

            # === THE SINGLE CALL — all intelligence lives in the engine ===
            result = engine.query(user_input, history)

            st.markdown(result["answer"])

            if result["sources"]:
                with st.expander("📚 View Evidence Citations"):
                    for r in result["sources"]:
                        st.markdown(f'<div class="micro-ref"><b>{r["type"].upper()}</b> | {r["source"]} — <i>{r["title"]}</i></div>', unsafe_allow_html=True)

            st.session_state.messages.append({
                "role": "assistant",
                "content": result["answer"],
                "sources": result.get("sources", []),
            })
