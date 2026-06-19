"""
MicroHeal Clinical Engine — The Core Brain
===========================================
Platform-independent engine. Import from ANY system:
  - Streamlit (app.py)
  - WhatsApp bot
  - FastAPI / Flask
  - n8n / workflow automation

Usage:
    from clinical_engine import ClinicalEngine

    gastro = ClinicalEngine("gastro")
    result = gastro.query("What causes GERD?")
    print(result["answer"])
    print(result["sources"])

    cardio = ClinicalEngine("cardio")ho
    result = cardio.query("Atrial fibrillation management")
"""

import json
import os
import re
import glob
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
if Path(".env").exists():
    load_dotenv()


# ──────────────────────────────────────────────────────────────────
#  Configuration
# ──────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent

DOMAIN_CONFIG = {
    "gastro": {
        "label": "Gastroenterology",
        "index_dir": BASE_DIR / "GastroRAG" / "index",
        "other_label": "Cardiology, Nephrology, Neurology, Gynecology, Oncology, Orthopedics, or Geriatrics",
        "other_key": "cardio, nephro, neuro, gyneco, onco, ortho, or geriatric",
    },
    "cardio": {
        "label": "Cardiology",
        "index_dir": BASE_DIR / "CardioRAG" / "index",
        "other_label": "Gastroenterology, Nephrology, Neurology, Gynecology, Oncology, Orthopedics, or Geriatrics",
        "other_key": "gastro, nephro, neuro, gyneco, onco, ortho, or geriatric",
    },
    "nephro": {
        "label": "Nephrology",
        "index_dir": BASE_DIR / "NephroRAG" / "index",
        "other_label": "Gastroenterology, Cardiology, Neurology, Gynecology, Oncology, Orthopedics, or Geriatrics",
        "other_key": "gastro, cardio, neuro, gyneco, onco, ortho, or geriatric",
    },
    "neuro": {
        "label": "Neurology",
        "index_dir": BASE_DIR / "NeuroRAG" / "index",
        "other_label": "Gastroenterology, Cardiology, Nephrology, Gynecology, Oncology, Orthopedics, or Geriatrics",
        "other_key": "gastro, cardio, nephro, gyneco, onco, ortho, or geriatric",
    },
    "gyneco": {
        "label": "Gynecology",
        "index_dir": BASE_DIR / "GynecoRAG" / "index",
        "other_label": "Gastroenterology, Cardiology, Nephrology, Neurology, Oncology, Orthopedics, or Geriatrics",
        "other_key": "gastro, cardio, nephro, neuro, onco, ortho, or geriatric",
    },
    "onco": {
        "label": "Oncology",
        "index_dir": BASE_DIR / "OncoRAG" / "index",
        "other_label": "Gastroenterology, Cardiology, Nephrology, Neurology, Gynecology, Orthopedics, or Geriatrics",
        "other_key": "gastro, cardio, nephro, neuro, gyneco, ortho, or geriatric",
    },
    "ortho": {
        "label": "Orthopedics",
        "index_dir": BASE_DIR / "OrthopedicsRAG" / "index",
        "other_label": "Gastroenterology, Cardiology, Nephrology, Neurology, Gynecology, Oncology, or Geriatrics",
        "other_key": "gastro, cardio, nephro, neuro, gyneco, onco, or geriatric",
    },
    "geriatric": {
        "label": "Geriatrics",
        "index_dir": BASE_DIR / "GeriatricRAG" / "index",
        "other_label": "Gastroenterology, Cardiology, Nephrology, Neurology, Gynecology, Oncology, or Orthopedics",
        "other_key": "gastro, cardio, nephro, neuro, gyneco, onco, or ortho",
    }
}


# ──────────────────────────────────────────────────────────────────
#  Retrieval Engine (no Streamlit dependency)
# ──────────────────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _load_registry(index_dir: Path) -> dict:
    """Dynamically scan and register all *_structure.json files."""
    registry = {}
    if not index_dir.exists():
        return registry

    for file in glob.glob(str(index_dir / "*_structure.json")):
        p = Path(file)
        doc_key = p.name.replace("_structure.json", "")
        short_name = doc_key.replace("-", " ").replace("_", " ").title()
        if len(short_name) > 45:
            short_name = short_name[:42] + "..."

        doc_type = "Guideline" if "guideline" in doc_key.lower() else "Reference"
        if "journal" in doc_key.lower() or "article" in doc_key.lower():
            doc_type = "Journal"
        elif "dataset" in doc_key.lower():
            doc_type = "Dataset"
        elif "book" in doc_key.lower():
            doc_type = "Textbook"

        registry[doc_key] = {
            "tree_path": p,
            "short": short_name,
            "type": doc_type,
        }

    return registry


def _get_candidates(query: str, tree_nodes: list, doc_short: str, doc_type: str, top_k: int = 12) -> list:
    q_norm = _normalize(query)
    keywords = [w for w in q_norm.split() if len(w) > 2]
    candidates = []

    def traverse(nodes):
        for n in nodes:
            score = 0
            t_norm = _normalize(n.get("title", ""))
            s_norm = _normalize(n.get("summary", ""))
            txt_norm = _normalize(n.get("text", n.get("content", "")))

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
                    "doc_type": doc_type,
                })

            if "nodes" in n:
                traverse(n["nodes"])

    traverse(tree_nodes)
    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[:top_k]


def _retrieve(query: str, registry: dict, domain_label: str) -> list:
    """Retrieve relevant context from the knowledge base."""
    expanded_q = _expand_query(query, domain_label)
    all_candidates = []

    for doc_key, doc_info in registry.items():
        tree_path = doc_info["tree_path"]
        if not tree_path.exists():
            continue
        try:
            with open(tree_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            structure = data.get("structure", data) if isinstance(data, dict) else data
            if not isinstance(structure, list):
                continue
            doc_candidates = _get_candidates(expanded_q, structure, doc_info["short"], doc_info["type"])
            all_candidates.extend(doc_candidates)
        except Exception:
            continue

    all_candidates.sort(key=lambda x: x["score"], reverse=True)
    best = _ai_rank(query, all_candidates[:30]) or all_candidates[:6]

    results = []
    for res in best[:6]:
        node = res["node"]
        full_text = node.get("text", node.get("content", "")).strip()
        summary = node.get("summary", "").strip()
        content = full_text[:2500] if full_text else summary[:1500]

        results.append({
            "source": res["doc_short"],
            "type": res["doc_type"],
            "title": node.get("title", "Unknown Section"),
            "content": content,
        })

    return results


# ──────────────────────────────────────────────────────────────────
#  LLM Integration (platform-independent)
# ──────────────────────────────────────────────────────────────────

def _load_config() -> dict:
    """Load config.yaml once and return as dict."""
    try:
        import yaml
        config_path = Path(__file__).parent / "config.yaml"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
                if isinstance(cfg, dict):
                    return cfg
    except Exception:
        pass
    return {}


def _get_default_model() -> str:
    """Read the model name from config.yaml in the parent directory of this file."""
    return _load_config().get("model", "gpt-4o-mini")


def _get_premium_model() -> str:
    """
    Retrieve the configured premium reasoning model.
    
    Attempts to read the 'premium_model' parameter from the root config.yaml file,
    defaulting to 'gpt-4o-mini' if not specified or config is unavailable.
    """
    return _load_config().get("premium_model", "gpt-4o-mini")


def _get_max_tokens() -> int:
    """
    Read the max_tokens setting from config.yaml.
    Defaults to 2000 if not specified — enough for detailed clinical answers.
    """
    return int(_load_config().get("max_tokens", 2000))


def _should_use_premium_model(question: str) -> bool:
    """
    Determine if a clinical query requires premium model reasoning capability.
    
    Forced to False to guarantee low cost (gpt-4o-mini only).
    """
    return False


def _llm_call(messages: list, temperature: float = 0.1, max_tokens: int = 2000, model: str = None) -> str:
    """Make an LLM call. Uses litellm if available, falls back to openai."""
    api_key = os.getenv("OPENAI_API_KEY")
    model_name = model or _get_default_model()
    print(f"[DEBUG] Calling LLM with model: {model_name}")
    try:
        import litellm
        try:
            from PageIndex.pageindex.utils import _core_token_callback
            import PageIndex.pageindex.utils as pi_utils
            if pi_utils.SESSION_START is None:
                pi_utils.SESSION_START = "clinical_engine_queries"
            pi_utils.CURRENT_PDF_STEM = "chat_queries"
            if not hasattr(litellm, "success_callback") or litellm.success_callback is None:
                litellm.success_callback = []
            if _core_token_callback not in litellm.success_callback:
                litellm.success_callback.append(_core_token_callback)
        except Exception as e_callback:
            print(f"[DEBUG] Callback registration failed: {e_callback}")
        
        response = litellm.completion(
            model=model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key,
        )
        return response.choices[0].message.content.strip()
    except ImportError:
        import openai
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()


def _expand_query(query: str, domain_label: str) -> str:
    try:
        prompt = f"Expand this {domain_label} medical query with full terms and synonyms. Query: '{query}'. Return ONLY the expanded version."
        result = _llm_call([{"role": "user", "content": prompt}], max_tokens=60, model="gpt-4o-mini")
        return result + " " + query
    except Exception:
        return query


def _ai_rank(query: str, candidates: list) -> list:
    if not candidates:
        return []
    context_list = []
    for i, c in enumerate(candidates):
        node = c["node"]
        preview = node.get("summary", "")[:800]
        context_list.append(f"[{i}] Source: {c['doc_short']} | Title: {node.get('title')} | Summary: {preview}")

    prompt = f"""You are a medical AI assistant. A user asked: "{query}"
From the list below, select the indices of the TOP 6 most medically relevant sections.
Return ONLY comma-separated indices like: 0, 2, 5, 8 or NONE.
{chr(10).join(context_list)}"""

    try:
        ans = _llm_call([{"role": "user", "content": prompt}], temperature=0, max_tokens=40, model="gpt-4o-mini")
        if "NONE" in ans.upper():
            return []
        indices = [int(i.strip()) for i in ans.split(",") if i.strip().isdigit()]
        return [candidates[i] for i in indices if i < len(candidates)]
    except Exception:
        return candidates[:5]


def _classify_query(query: str, domain_label: str, other_label: str) -> str:
    """
    Use the LLM to intelligently classify a query.
    Returns: 'in_domain', 'out_of_domain', or 'casual'
    No hardcoded keywords — pure LLM intelligence.
    """
    prompt = f"""You are a medical query classifier. Classify the following user message into exactly ONE category.

Active specialist: {domain_label}
Other available specialists: {other_label}

Categories to choose from:
- "in_domain" — The query is directly related to {domain_label}, or is a general medical/health query that a {domain_label} specialist can answer.
- "out_of_domain" — The query is CLEARLY and SPECIFICALLY about topics belonging to {other_label} and NOT {domain_label} (e.g., GERD or stomach issues when active is Nephrology/Cardiology, or heart attacks/ECGs when active is Gastroenterology/Nephrology).
- "casual" — Greetings, thanks, or general conversation.

Rule: If the query is specific to the other specialists ({other_label}), reply "out_of_domain".

User message: "{query}"

Reply with ONLY one word: in_domain, out_of_domain, or casual"""

    try:
        result = _llm_call(
            [{"role": "user", "content": prompt}],
            temperature=0, max_tokens=10, model="gpt-4o-mini"
        ).lower().strip().replace('"', '').replace("'", "")

        if "out" in result:
            return "out_of_domain"
        elif "casual" in result:
            return "casual"
        else:
            return "in_domain"
    except Exception:
        return "in_domain"  # Default: try to answer


def _normalize_source_name(name: str) -> str:
    """Normalize source name by lowercasing, stripping, compressing spaces, and removing non-alphanumeric chars."""
    if not name:
        return ""
    name = name.lower().strip()
    name = re.sub(r"\s+", " ", name)
    name = re.sub(r"[^a-z0-9\s]", "", name)
    return name.strip()


def _source_matches(r_source: str, used_names: list) -> bool:
    """Check if the registry source name matches any of the names in used_names robustly."""
    r_norm = _normalize_source_name(r_source)
    if not r_norm:
        return False
    for u in used_names:
        u_norm = _normalize_source_name(u)
        if not u_norm:
            continue
        if u_norm == r_norm or u_norm in r_norm or r_norm in u_norm:
            return True
    return False


# ──────────────────────────────────────────────────────────────────
#  ClinicalEngine — The Main Class
# ──────────────────────────────────────────────────────────────────

class ClinicalEngine:
    """
    A self-contained, domain-strict clinical specialist.

    Usage:
        engine = ClinicalEngine("gastro")   # or "cardio"
        result = engine.query("What is GERD?")
        # result = {
        #   "answer": "...",
        #   "sources": [...],       # only real sources, empty if none used
        #   "domain": "Gastroenterology",
        #   "out_of_domain": False
        # }
    """

    def __init__(self, domain: str):
        """Initialize with 'gastro', 'cardio', 'nephro', 'neuro', 'gyneco', 'onco', 'ortho', or 'geriatric'."""
        domain = domain.lower().strip()
        if domain not in DOMAIN_CONFIG:
            raise ValueError(f"Invalid domain '{domain}'. Use 'gastro', 'cardio', 'nephro', 'neuro', 'gyneco', 'onco', 'ortho', or 'geriatric'.")

        self.config = DOMAIN_CONFIG[domain]
        self.domain = domain
        self.label = self.config["label"]
        self.other_label = self.config["other_label"]
        self.registry = _load_registry(self.config["index_dir"])

    def query(self, question: str, history: list = None) -> dict:
        """
        Main query endpoint. Returns a structured dict.

        Args:
            question: The user's question.
            history: Optional list of {"role": "user"/"assistant", "content": "..."} dicts.

        Returns:
            dict with keys: answer, sources, domain, out_of_domain
        """
        history = history or []

        # Dynamically determine the appropriate model tier (standard vs premium) for response generation
        use_premium = _should_use_premium_model(question)
        response_model = _get_premium_model() if use_premium else _get_default_model()

        # 1. Use LLM to intelligently classify the query (no hardcoded keywords)
        classification = _classify_query(question, self.label, self.other_label)

        # 2. Handle out-of-domain
        if classification == "out_of_domain":
            try:
                redirect_prompt = (
                    f"You are MicroHeal Clinical Bot, the {self.label} specialist. "
                    f"The user asked a question about {self.other_label}. "
                    f"Politely tell them this is outside your specialty and suggest they "
                    f"switch to the {self.other_label} model. Keep it professional and brief. "
                    f"DO NOT end your response with repetitive sign-offs, signatures, or greetings (e.g., 'Take care!', 'Take care of yourself!'). Keep the ending clean."
                )
                answer = _llm_call([
                    {"role": "system", "content": redirect_prompt},
                    {"role": "user", "content": question}
                ], temperature=0.3, max_tokens=100, model="gpt-4o-mini")
            except Exception:
                answer = (
                    f"This question falls under {self.other_label}. "
                    f"Please switch to the {self.other_label} model for the best answer."
                )

            return {
                "answer": answer,
                "sources": [],
                "domain": self.label,
                "out_of_domain": True,
            }

        # 3. Handle casual conversation
        if classification == "casual":
            try:
                answer = _llm_call([
                    {"role": "system", "content": (
                        f"You are MicroHeal Clinical Bot, a friendly and dedicated {self.label} "
                        f"specialist AI. Respond naturally to the user. Keep it professional and conversational. "
                        f"You specialize in {self.label}. "
                        f"DO NOT end your response with repetitive sign-offs, signatures, or greetings (e.g., 'Take care!', 'Take care of yourself!'). Keep the ending clean."
                    )},
                    {"role": "user", "content": question}
                ], temperature=0.5, max_tokens=200, model="gpt-4o-mini")
            except Exception:
                answer = f"Hello! I'm your {self.label} specialist. How can I help you today?"

            return {
                "answer": answer,
                "sources": [],
                "domain": self.label,
                "out_of_domain": False,
            }

        # 4. Clinical question — retrieve from knowledge base
        context_results = _retrieve(question, self.registry, self.label)

        # Detect Hindi/Hinglish
        wants_hindi = any(w in question.lower() for w in ["btao", "kya", "hai", "mujhe", "kaise"])
        lang = "Respond in Hindi/Hinglish." if wants_hindi else "Respond in English."

        if context_results:
            # 5a. Context found — answer STRICTLY from knowledge base
            ctx_text = "\n\n".join([
                f"Source: {r['source']}\nTitle: {r['title']}\nContent: {r['content']}"
                for r in context_results
            ])

            system_prompt = f"""You are MicroHeal Clinical Bot, a dedicated {self.label} specialist. {lang}

You are EXCLUSIVELY a {self.label} specialist. Respond with the professionalism, authority, and tone of a medical doctor/clinical expert.

RULES:
- Answer the question naturally, clearly, and professionally. Use a formal, expert clinical tone.
- DO NOT end your response with repetitive sign-offs, signatures, or greetings (e.g., 'Take care!', 'Take care of yourself!', 'Wishing you the best!', 'Dr. Bot'). Keep the response ending clean and medical.
- Keep your answers strictly within the domain of {self.label}. Do not provide diagnostics or clinical guidance for conditions outside of your specialty.
- Prioritize using the provided context first to formulate the core clinical facts and details of your response.
- Conclude and supplement the response using your general {self.label} clinical knowledge where the context is incomplete or silent, ensuring the answer is cohesive, comprehensive, and natural. Do not write phrases like 'based on the context' or mention the source documents in your text.
- DO NOT mention source names or use inline citations in your text response.
- FORMATTING: NEVER use markdown headers (# or ##). For headings, use plain text or bold text with a colon (e.g., *Heading Name:*).
- FORMATTING: Use a single asterisk for bold text (e.g., *Bold Text*). NEVER use double asterisks (**).
- FORMATTING: For bullet points, use a single bullet character (•). DO NOT use dashes (-) or asterisks (*) for bullets.
- At the very end of your response, you MUST append the list of source names from the context that are related to the query topic inside XML tags like this:
  <sources>Source Name 1, Source Name 2</sources>
  If no sources from the context were useful or related to the query, you MUST write:
  <sources>None</sources>

Context:
{ctx_text}"""

            messages = [{"role": "system", "content": system_prompt}]
            for msg in history[-4:]:
                messages.append({"role": msg["role"], "content": msg["content"][:1500]})
            messages.append({"role": "user", "content": question})

            try:
                answer = _llm_call(messages, temperature=0.1, max_tokens=_get_max_tokens(), model=response_model)
                # Parse the <sources>...</sources> tag from the response
                import re
                sources_match = re.search(r"<sources>(.*?)</sources>", answer, re.IGNORECASE | re.DOTALL)
                if sources_match:
                    sources_str = sources_match.group(1).strip()
                    # Strip the tags and their content from the final answer
                    answer = re.sub(r"<sources>.*?</sources>", "", answer, flags=re.IGNORECASE | re.DOTALL).strip()
                    
                    if "none" in sources_str.lower():
                        # Fallback: keep all context_results if they are medically relevant (rather than clearing them to [])
                        # this ensures references still appear for clinical queries even if LLM wrote "None"
                        pass
                    else:
                        used_names = [s.strip() for s in sources_str.split(",") if s.strip()]
                        matched_results = [r for r in context_results if _source_matches(r["source"], used_names)]
                        # Fallback: only narrow down if matched_results is not empty, otherwise keep all as fallback
                        if matched_results:
                            context_results = matched_results
                else:
                    # Fallback: if the tag is missing, keep the context_results rather than clearing to []
                    # but strip the tag in case it was half-formed
                    answer = re.sub(r"<sources>.*?</sources>", "", answer, flags=re.IGNORECASE | re.DOTALL).strip()
            except Exception as e:
                answer = f"Error generating response: {str(e)}"
                context_results = []

            return {
                "answer": answer,
                "sources": context_results,
                "domain": self.label,
                "out_of_domain": False,
            }

        else:
            # 5b. No context found — answer from LLM general knowledge, NO sources
            system_prompt = f"""You are MicroHeal Clinical Bot, a dedicated {self.label} specialist. {lang}

You are EXCLUSIVELY a {self.label} specialist.
Answer from your general {self.label} medical knowledge.
Be helpful, formal, and accurate. Use an expert clinical tone.
DO NOT end your response with repetitive sign-offs, signatures, or greetings (e.g., 'Take care!', 'Take care of yourself!'). Keep the ending clean and professional.
- FORMATTING: NEVER use markdown headers (# or ##). For headings, use plain text or bold text with a colon (e.g., *Heading Name:*).
- FORMATTING: Use a single asterisk for bold text (e.g., *Bold Text*). NEVER use double asterisks (**).
- FORMATTING: For bullet points, use a single bullet character (•). DO NOT use dashes (-) or asterisks (*) for bullets."""

            messages = [{"role": "system", "content": system_prompt}]
            for msg in history[-4:]:
                messages.append({"role": msg["role"], "content": msg["content"][:1500]})
            messages.append({"role": "user", "content": question})

            try:
                answer = _llm_call(messages, temperature=0.2, max_tokens=_get_max_tokens(), model=response_model)
            except Exception as e:
                answer = f"Error generating response: {str(e)}"

            # NO sources — answered from general LLM knowledge
            return {
                "answer": answer,
                "sources": [],
                "domain": self.label,
                "out_of_domain": False,
            }

    def get_source_count(self) -> int:
        """Return number of indexed documents."""
        return len(self.registry)


# ──────────────────────────────────────────────────────────────────
#  Standalone Test
# ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("MicroHeal Clinical Engine — Self-Test")
    print("=" * 60)

    gastro = ClinicalEngine("gastro")
    print(f"\n[GASTRO] Loaded {gastro.get_source_count()} sources")

    cardio = ClinicalEngine("cardio")
    print(f"[CARDIO] Loaded {cardio.get_source_count()} sources")

    nephro = ClinicalEngine("nephro")
    print(f"[NEPHRO] Loaded {nephro.get_source_count()} sources")

    neuro = ClinicalEngine("neuro")
    print(f"[NEURO] Loaded {neuro.get_source_count()} sources")

    gyneco = ClinicalEngine("gyneco")
    print(f"[GYNECO] Loaded {gyneco.get_source_count()} sources")

    onco = ClinicalEngine("onco")
    print(f"[ONCO] Loaded {onco.get_source_count()} sources")

    ortho = ClinicalEngine("ortho")
    print(f"[ORTHO] Loaded {ortho.get_source_count()} sources")

    geriatric = ClinicalEngine("geriatric")
    print(f"[GERIATRIC] Loaded {geriatric.get_source_count()} sources")

    print(f"\n[CONFIG] max_tokens = {_get_max_tokens()}")

    # Test domain isolation
    print("\n--- Domain Isolation Test ---")
    result = gastro.query("What is atrial fibrillation?")
    print(f"Gastro asked about cardio -> out_of_domain={result['out_of_domain']}, sources={len(result['sources'])}")
    print(f"Answer: {result['answer']}")

    result = cardio.query("What is stomach pain?")
    print(f"\nCardio asked about gastro -> out_of_domain={result['out_of_domain']}, sources={len(result['sources'])}")
    print(f"Answer: {result['answer']}")

    result = nephro.query("What is GERD or stomach pain?")
    print(f"\nNephro asked about gastro -> out_of_domain={result['out_of_domain']}, sources={len(result['sources'])}")
    print(f"Answer: {result['answer']}")

    # Test casual
    print("\n--- Greeting Test ---")
    result = gastro.query("Hey, how are you?")
    print(f"Sources: {len(result['sources'])}")
    print(f"Answer: {result['answer']}")
