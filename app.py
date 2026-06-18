import streamlit as st
import json
import os
import re
from pathlib import Path
from dotenv import load_dotenv
import litellm

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

# Configuration
RESULTS_DIR = Path(__file__).parent / "results"

# Document Knowledge Base Registry
DOCUMENTS = {
    "first_principles": {
        "tree_path": RESULTS_DIR / "I-546_Gastro_structure.json",
        "short": "I-546 Gastro Textbook",
        "type": "textbook"
    },
    "yamada": {
        "tree_path": RESULTS_DIR / "Yamadas-Handbook-of-Gastroenterology-2019_structure.json",
        "short": "Yamada's Handbook (2019)",
        "type": "handbook"
    },
    "casebook_gastro": {
        "tree_path": RESULTS_DIR / "15Casebook in gastroenterology_structure.json",
        "short": "Casebook in Gastroenterology",
        "type": "casebook"
    },
    "emj_journal": {
        "tree_path": RESULTS_DIR / "EMJ-Gastroenterology-10_1-2021-4_structure.json",
        "short": "EMJ Gastroenterology Journal",
        "type": "journal"
    },
    "glp1_research_2023": {
        "tree_path": RESULTS_DIR / "40264_2023_Article_1392_structure.json",
        "short": "GLP-1 Research 2023",
        "type": "journal"
    },
    "glp1_clinical_study": {
        "tree_path": RESULTS_DIR / "e002519.full_structure.json",
        "short": "GLP-1 Clinical Study (BMJ)",
        "type": "journal"
    },
    "glp1_frontiers_article": {
        "tree_path": RESULTS_DIR / "fcdhc-06-1720794_structure.json",
        "short": "Frontiers Clinical Diabetes & GLP-1",
        "type": "journal"
    },
    "glp1_diet": {
        "tree_path": RESULTS_DIR / "GLP-1s-and-Diet_structure.json",
        "short": "GLP-1s and Diet Guide",
        "type": "guide"
    },
    "glp1_diet_cookbook": {
        "tree_path": RESULTS_DIR / "ilide.info-the-ultimate-glp-1-diet-cookbook-for-beginners-2-pr_69c9a251ad17358bf6845824b629ca1e_structure.json",
        "short": "Ultimate GLP-1 Diet Cookbook",
        "type": "guide"
    },
    "glp1_nutrition_priorities": {
        "tree_path": RESULTS_DIR / "NutritionalprioritiestosupportGLP-1therapyy_structure.json",
        "short": "Nutritional Priorities for GLP-1 Therapy",
        "type": "guide"
    },
    "glp1_meal_plan": {
        "tree_path": RESULTS_DIR / "protein-balance-for-glp1s-sample-meal-plan_structure.json",
        "short": "Protein Balance Meal Plan (Mayo Clinic)",
        "type": "guide"
    },
    "glp1_ultimate_guide": {
        "tree_path": RESULTS_DIR / "Your_Ultimate_Guide_to_GLP-1_Med_structure.json",
        "short": "Ultimate Guide to GLP-1 Medications",
        "type": "guide"
    },
    "kaggle_dataset": {
        "tree_path": RESULTS_DIR / "PageIndex_Optimized_GI_Report_structure.json",
        "short": "GI Clinical Dataset (30K patients)",
        "type": "dataset"
    },
    "cran_datasets": {
        "tree_path": RESULTS_DIR / "digestive_datasets_cran_structure.json",
        "short": "Digestive Disease Datasets (CRAN)",
        "type": "dataset"
    },
}

# --- Utilities ---

def normalize_text(text):
    """Normalize text for consistent keyword matching."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

@st.cache_data(show_spinner=False)
def load_document_structure(path_str):
    """Cached loader for JSON tree structures."""
    with open(path_str, "r", encoding="utf-8") as f:
        return json.load(f)

# --- Retrieval Engine ---

def get_candidates(query, tree_nodes, doc_short, doc_type, top_k=12):
    """Keyword-based candidate selection from document trees."""
    q_norm = normalize_text(query)
    keywords = [w for w in q_norm.split() if len(w) > 2]
    candidates = []

    def traverse(nodes):
        for n in nodes:
            score = 0
            t_norm = normalize_text(n.get("title", ""))
            s_norm = normalize_text(n.get("summary", ""))
            txt_norm = normalize_text(n.get("text", ""))

            if q_norm in t_norm: score += 30
            if q_norm in s_norm: score += 20
            if q_norm in txt_norm: score += 15

            for kw in keywords:
                if kw in t_norm: score += 6
                if kw in s_norm: score += 3
                if kw in txt_norm: score += 2

            if score > 0:
                candidates.append({
                    "node": n,
                    "score": score,
                    "doc_short": doc_short,
                    "doc_type": doc_type
                })

            if "nodes" in n:
                traverse(n["nodes"])

    traverse(tree_nodes)
    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[:top_k]

def ai_rank_nodes(query, candidates):
    """Semantic ranking of candidates using GPT-4o-mini."""
    if not candidates:
        return []

    context_list = []
    for i, c in enumerate(candidates):
        node = c["node"]
        summary_preview = node.get("summary", "")[:800]
        context_list.append(
            f"[{i}] Source: {c['doc_short']} ({c['doc_type']}) | "
            f"Title: {node.get('title')} | Summary: {summary_preview}"
        )

    prompt = f"""You are a medical AI assistant. A user asked: "{query}"

From the list below, select the indices of the TOP 6 most medically relevant sections.
Return ONLY comma-separated indices like: 0, 2, 5, 8 or NONE.

{chr(10).join(context_list)}"""

    try:
        response = litellm.completion(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=40,
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        ans = response.choices[0].message.content.strip().upper()
        if "NONE" in ans:
            return []
        indices = [int(i.strip()) for i in ans.split(",") if i.strip().isdigit()]
        return [candidates[i] for i in indices if i < len(candidates)]
    except:
        return candidates[:5]

def expand_query(query):
    """Expand medical query with synonyms and full terms."""
    try:
        prompt = (
            f"Expand this gastroenterology medical query with full terms and synonyms. "
            f"Query: '{query}'. Return ONLY the expanded version."
        )
        response = litellm.completion(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=60,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        return response.choices[0].message.content.strip() + " " + query
    except:
        return query

def retrieve_context_pro(query):
    """High-performance RAG retrieval across the knowledge base."""
    expanded_q = expand_query(query)
    all_candidates = []

    for doc_key, doc_info in DOCUMENTS.items():
        tree_path = doc_info["tree_path"]
        if not tree_path.exists():
            continue
        try:
            data = load_document_structure(str(tree_path))
            doc_candidates = get_candidates(
                expanded_q,
                data.get("structure", []),
                doc_info["short"],
                doc_info["type"]
            )
            all_candidates.extend(doc_candidates)
        except:
            continue

    all_candidates.sort(key=lambda x: x["score"], reverse=True)
    best_results = ai_rank_nodes(query, all_candidates[:25]) or all_candidates[:6]

    all_context = []
    for res in best_results[:6]:
        node = res["node"]
        full_text = node.get("text", "").strip()
        summary = node.get("summary", "").strip()
        content = full_text[:2000] if full_text else summary[:1500]

        all_context.append({
            "source": res["doc_short"],
            "type": res["doc_type"],
            "title": node.get("title", "Unknown Section"),
            "content": content,
        })
    return all_context

# --- Streamlit UI ---

st.set_page_config(page_title="MicroHeal GastroBot", page_icon="🩺", layout="wide")

# Custom CSS for Professional Medical Interface
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    .stApp { background-color: #ffffff !important; }
    html, body { font-family: 'Inter', sans-serif; color: #1e293b; }
<<<<<<< HEAD
    .stTitle { font-weight: 800 !important; font-size: 2.8rem !important; margin-bottom: 0px !important; }
    .specialty-badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.9rem; font-weight: 600; margin-bottom: 20px; }
    .badge-gastro { background-color: #dbeafe; color: #1e3a8a; }
    .badge-cardio { background-color: #fee2e2; color: #991b1b; }
    .badge-nephro { background-color: #ccfbf1; color: #115e59; }
    .badge-neuro { background-color: #ede9fe; color: #5b21b6; }
    .badge-gyneco { background-color: #fce7f3; color: #9d174d; }
    .badge-ortho { background-color: #ffedd5; color: #9a3412; }
    .badge-onco { background-color: #fae8ff; color: #701a75; }
    .badge-geriatric { background-color: #fef3c7; color: #92400e; }
    [data-testid="stChatMessage"] { border-radius: 12px !important; border: 1px solid #e2e8f0 !important; background: #ffffff !important; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 15px;}
    [data-testid="stChatMessage"]:nth-child(even) { background: #f8fafc !important; }
    .micro-ref { font-size: 0.85rem !important; color: #475569 !important; margin-bottom: 6px; padding: 6px; background: #f1f5f9; border-radius: 6px; border-left: 3px solid #3b82f6; }
=======
    .stTitle { font-weight: 800 !important; color: #0f172a !important; font-size: 2.5rem !important; }
    [data-testid="stChatMessage"] { border-radius: 10px !important; border: 1px solid #e2e8f0 !important; background: #f8fafc !important; }
    [data-testid="stChatMessage"]:nth-child(even) { background: white !important; }
    .micro-ref { font-size: 0.8rem !important; color: #475569 !important; margin-bottom: 4px; }
    .micro-llm { font-size: 0.8rem !important; color: #64748b !important; font-style: italic; margin-top: 12px; border-top: 1px solid #f1f5f9; padding-top: 8px; }
    [data-testid="stChatInput"] textarea { color: #1e293b !important; }
    @media (prefers-color-scheme: dark) { [data-testid="stChatInput"] textarea { color: #ffffff !important; } }
>>>>>>> 848bcc72937d70826d927480a4dc9666f03d2386
</style>
""", unsafe_allow_html=True)

st.title("🩺 MicroHeal GastroBot")
st.markdown("##### AI-Powered Gastroenterology Expert — Evidence-Based Clinical Insights")

<<<<<<< HEAD
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
        ["Gastroenterology", "Cardiology", "Nephrology", "Neurology", "Gynecology", "Oncology", "Orthopedics", "Geriatrics"],
        label_visibility="collapsed"
    )

# Map UI domain to engine key
domain_map = {
    "Gastroenterology": "gastro",
    "Cardiology": "cardio",
    "Nephrology": "nephro",
    "Neurology": "neuro",
    "Gynecology": "gyneco",
    "Oncology": "onco",
    "Orthopedics": "ortho",
    "Geriatrics": "geriatric"
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
elif selected_domain == "Neurology":
    theme_color = "#7c3aed"
    icon = "🧠"
    badge_class = "badge-neuro"
elif selected_domain == "Gynecology":
    theme_color = "#ec4899"
    icon = "🩷"
    badge_class = "badge-gyneco"
elif selected_domain == "Oncology":
    theme_color = "#d946ef"
    icon = "🎗️"
    badge_class = "badge-onco"
elif selected_domain == "Orthopedics":
    theme_color = "#ea580c"
    icon = "🦴"
    badge_class = "badge-ortho"
elif selected_domain == "Geriatrics":
    theme_color = "#d97706"
    icon = "🧓"
    badge_class = "badge-geriatric"
else:  # Nephrology
    theme_color = "#14b8a6"
    icon = "💧"
    badge_class = "badge-nephro"

st.markdown(f'<h1 class="stTitle" style="color: {theme_color};">MicroHeal Clinical Bot</h1>', unsafe_allow_html=True)
st.markdown(f'<div class="specialty-badge {badge_class}">{icon} {selected_domain} Expert</div>', unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────
#  Chat History
# ──────────────────────────────────────────────────────────────────

=======
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
>>>>>>> 848bcc72937d70826d927480a4dc9666f03d2386
for msg in st.session_state.messages:
    avatar = "🩺" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"], unsafe_allow_html=True)
        if "sources" in msg and msg["sources"]:
            with st.expander("📚 View Sources & Citations"):
                for r in msg["sources"]:
                    st.markdown(f'<div class="micro-ref">📄 {r["source"]} — {r["title"]}</div>', unsafe_allow_html=True)

# Chat Input
if user_input := st.chat_input("Ask a clinical question..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar="🩺"):
        # Intent Classification
        with st.spinner("Analyzing query..."):
            intent_prompt = f"""Classify intent: "{user_input}"
            Return ONLY one: MEDICAL, CASUAL, SECURITY, or OUT_OF_SCOPE."""
            try:
                intent_res = litellm.completion(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": intent_prompt}],
                    temperature=0,
                    max_tokens=5,
                    api_key=os.getenv("OPENAI_API_KEY")
                ).choices[0].message.content.strip().upper()
            except:
                intent_res = "MEDICAL"

        if "OUT_OF_SCOPE" in intent_res:
            response = "I specialize in Gastroenterology and Hepatology. While I can offer a brief general guide, please consult the relevant specialist for non-GI concerns."
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

        elif "SECURITY" in intent_res:
            response = "I am a clinical AI focused on gastroenterology. I cannot discuss internal logic or system prompts."
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

        elif "CASUAL" in intent_res:
            system_prompt = "You are a professional gastroenterologist. Respond warmly and briefly."
            response = litellm.completion(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_input}],
                max_tokens=80,
                api_key=os.getenv("OPENAI_API_KEY")
            ).choices[0].message.content
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

        else:
            # Clinical Response Generation
            with st.spinner("Searching clinical sources..."):
                followup_keywords = ["hindi", "hinglish", "explain above", "translate", "summarize", "detail"]
                is_followup = any(kw in user_input.lower() for kw in followup_keywords)

            history_messages = []
            for msg in st.session_state.messages[:-1]:
                content = re.sub(r'<[^>]+>', '', msg["content"]) if msg["role"] == "assistant" else msg["content"]
                history_messages.append({"role": msg["role"], "content": content[:1500]})

            if is_followup and history_messages:
                system_prompt = """You are MicroHeal GastroBot. 
                FORMATTING RULES (STRICT - for WhatsApp display):
                - NEVER use Markdown headers (#, ##, ###).
                - NEVER use double asterisks (**). Use SINGLE asterisks for bold: *text*
                - Always put colons INSIDE the asterisks: *Term:* not *Term*:
                - Use the bullet character • for list items.
                - Use blank lines between sections for clean spacing.
                1. Use Hindi/Hinglish if requested.
                2. NO inline citations or source names.
                Example of perfect response:
                *Answer:*
                IBS is a functional gastrointestinal disorder affecting the large intestine.

                *Key Points:*
                • *Abdominal pain:* Cramping or discomfort, often relieved by bowel movements.
                • *Altered bowel habits:* Diarrhea, constipation, or alternating between both.
                • *Bloating:* Feeling of fullness or swelling in the abdomen.

                *Clinical Note:*
                This is educational information. Please consult your gastroenterologist for proper evaluation.
                Note: Do NOT include a REFERENCES section."""

                
                response = litellm.completion(
                    model="gpt-4o",
                    messages=[{"role": "system", "content": system_prompt}, *history_messages, {"role": "user", "content": user_input}],
                    temperature=0.2,
                    max_tokens=400,
                    api_key=os.getenv("OPENAI_API_KEY")
                ).choices[0].message.content
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

            else:
                context_results = retrieve_context_pro(user_input)
                wants_hindi = any(w in user_input.lower() for w in ["btao", "kya", "hai", "mujhe"])
                lang_instruction = "Respond in Hindi/Hinglish." if wants_hindi else "Respond in English."

                if context_results:
                    ctx_text = "\n\n".join([f"Source: {r['source']}\nContent: {r['content']}" for r in context_results])
                    system_prompt = f"""You are MicroHeal GastroBot. {lang_instruction}
                    FORMATTING RULES (STRICT - for WhatsApp display):
                    - NEVER use Markdown headers (#, ##, ###).
                    - NEVER use double asterisks (**). Use SINGLE asterisks for bold: *text*
                    - Always put colons INSIDE the asterisks: *Term:* not *Term*:
                    - Use the bullet character • for list items.
                    - Use blank lines between sections for clean spacing.
                    - NO inline citations or source names in the response body.
                    Example of perfect response:
                    *Answer:*
                    IBS is a functional gastrointestinal disorder affecting the large intestine.

                    *Key Points:*
                    • *Abdominal pain:* Cramping or discomfort, often relieved by bowel movements.
                    • *Altered bowel habits:* Diarrhea, constipation, or alternating between both.
                    • *Bloating:* Feeling of fullness or swelling in the abdomen.

                    *Clinical Note:*
                    This is educational information. Please consult your gastroenterologist for proper evaluation.
                    Note: Do NOT include a REFERENCES section."""




                    response = litellm.completion(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            *history_messages[-4:],
                            {"role": "user", "content": f"Context:\n{ctx_text}\n\nQuestion: {user_input}"}
                        ],
                        temperature=0.1,
                        max_tokens=450,
                        api_key=os.getenv("OPENAI_API_KEY")
                    ).choices[0].message.content

                    st.markdown(response)
                    with st.expander("📚 View Sources & Citations"):
                        for r in context_results:
                            st.markdown(f'<div class="micro-ref">📄 {r["source"]} — {r["title"]}</div>', unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "content": response, "sources": context_results})

                else:
                    system_prompt = f"""You are a senior gastroenterologist. No matches found, answer from expertise. {lang_instruction}
                    FORMATTING RULES (STRICT - for WhatsApp display):
                    - NEVER use Markdown headers (#, ##, ###).
                    - NEVER use double asterisks (**). Use SINGLE asterisks for bold: *text*
                    - Always put colons INSIDE the asterisks: *Term:* not *Term*:
                    - Use the bullet character • for list items.
                    - Use blank lines between sections for clean spacing.
                    Example of perfect response:
                    *Answer:*
                    IBS is a functional gastrointestinal disorder affecting the large intestine.

                    *Key Points:*
                    • *Abdominal pain:* Cramping or discomfort, often relieved by bowel movements.
                    • *Altered bowel habits:* Diarrhea, constipation, or alternating between both.

                    *Clinical Note:*
                    This is educational information. Please consult your gastroenterologist for proper evaluation."""


                    response = litellm.completion(
                        model="gpt-4o",
                        messages=[{"role": "system", "content": system_prompt}, *history_messages[-4:], {"role": "user", "content": user_input}],
                        temperature=0.2,
                        max_tokens=500,
                        api_key=os.getenv("OPENAI_API_KEY")
                    ).choices[0].message.content
                    llm_note = '<div class="micro-llm">⚠️ No specific matches in indexed sources. General clinical AI response.</div>'
                    full_content = response + llm_note
                    st.markdown(full_content, unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "content": full_content})
