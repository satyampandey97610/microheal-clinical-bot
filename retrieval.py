"""
GastroRAG retrieval over PageIndex JSON trees (results/*_structure.json).
Used by the FastAPI service and optionally by the Streamlit UI.
"""
from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import litellm
from dotenv import load_dotenv


def _load_env() -> None:
    """Local .env first; then repo-root / agentic-chatbot .env as fallback."""
    root = Path(__file__).resolve().parent
    for env_path in (
        root.parent / ".env",
        root.parent / "agentic-chatbot" / ".env",
        root / ".env",
    ):
        if env_path.is_file():
            load_dotenv(env_path, override=True)


_load_env()

RESULTS_DIR = Path(
    os.getenv("GASTRO_RAG_RESULTS_DIR", str(Path(__file__).parent / "results"))
).resolve()

RETRIEVE_MODEL = os.getenv("RAG_RETRIEVE_MODEL", "gpt-4o-mini")

DOCUMENTS: Dict[str, Dict[str, Any]] = {
    "first_principles": {
        "tree_path": RESULTS_DIR / "I-546_Gastro_structure.json",
        "short": "I-546 Gastro Textbook",
        "type": "textbook",
    },
    "yamada": {
        "tree_path": RESULTS_DIR / "Yamadas-Handbook-of-Gastroenterology-2019_structure.json",
        "short": "Yamada's Handbook (2019)",
        "type": "handbook",
    },
    "casebook_gastro": {
        "tree_path": RESULTS_DIR / "15Casebook in gastroenterology_structure.json",
        "short": "Casebook in Gastroenterology",
        "type": "casebook",
    },
    "emj_journal": {
        "tree_path": RESULTS_DIR / "EMJ-Gastroenterology-10_1-2021-4_structure.json",
        "short": "EMJ Gastroenterology Journal",
        "type": "journal",
    },
    "glp1_research_2023": {
        "tree_path": RESULTS_DIR / "40264_2023_Article_1392_structure.json",
        "short": "GLP-1 Research 2023",
        "type": "journal",
    },
    "glp1_clinical_study": {
        "tree_path": RESULTS_DIR / "e002519.full_structure.json",
        "short": "GLP-1 Clinical Study (BMJ)",
        "type": "journal",
    },
    "glp1_frontiers_article": {
        "tree_path": RESULTS_DIR / "fcdhc-06-1720794_structure.json",
        "short": "Frontiers Clinical Diabetes & GLP-1",
        "type": "journal",
    },
    "glp1_diet": {
        "tree_path": RESULTS_DIR / "GLP-1s-and-Diet_structure.json",
        "short": "GLP-1s and Diet Guide",
        "type": "guide",
    },
    "glp1_diet_cookbook": {
        "tree_path": RESULTS_DIR
        / "ilide.info-the-ultimate-glp-1-diet-cookbook-for-beginners-2-pr_69c9a251ad17358bf6845824b629ca1e_structure.json",
        "short": "Ultimate GLP-1 Diet Cookbook",
        "type": "guide",
    },
    "glp1_nutrition_priorities": {
        "tree_path": RESULTS_DIR / "NutritionalprioritiestosupportGLP-1therapyy_structure.json",
        "short": "Nutritional Priorities for GLP-1 Therapy",
        "type": "guide",
    },
    "glp1_meal_plan": {
        "tree_path": RESULTS_DIR / "protein-balance-for-glp1s-sample-meal-plan_structure.json",
        "short": "Protein Balance Meal Plan (Mayo Clinic)",
        "type": "guide",
    },
    "glp1_ultimate_guide": {
        "tree_path": RESULTS_DIR / "Your_Ultimate_Guide_to_GLP-1_Med_structure.json",
        "short": "Ultimate Guide to GLP-1 Medications",
        "type": "guide",
    },
    "kaggle_dataset": {
        "tree_path": RESULTS_DIR / "PageIndex_Optimized_GI_Report_structure.json",
        "short": "GI Clinical Dataset (30K patients)",
        "type": "dataset",
    },
    "cran_datasets": {
        "tree_path": RESULTS_DIR / "digestive_datasets_cran_structure.json",
        "short": "Digestive Disease Datasets (CRAN)",
        "type": "dataset",
    },
}


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


@lru_cache(maxsize=32)
def load_document_structure(path_str: str) -> dict:
    with open(path_str, "r", encoding="utf-8") as f:
        return json.load(f)


def count_documents_loaded() -> int:
    return sum(1 for d in DOCUMENTS.values() if d["tree_path"].exists())


def get_candidates(
    query: str, tree_nodes: list, doc_short: str, doc_type: str, top_k: int = 12
) -> list:
    q_norm = normalize_text(query)
    keywords = [w for w in q_norm.split() if len(w) > 2]
    candidates: list = []

    def traverse(nodes: list) -> None:
        for n in nodes:
            score = 0
            t_norm = normalize_text(n.get("title", ""))
            s_norm = normalize_text(n.get("summary", ""))
            txt_norm = normalize_text(n.get("text", ""))

            if q_norm in t_norm:
                score += 30
            if q_norm in s_norm:
                score += 20
            if q_norm in txt_norm:
                score += 15

            for kw in keywords:
                if kw in t_norm:
                    score += 6
                if kw in s_norm:
                    score += 3
                if kw in txt_norm:
                    score += 2

            if score > 0:
                candidates.append(
                    {
                        "node": n,
                        "score": score,
                        "doc_short": doc_short,
                        "doc_type": doc_type,
                    }
                )

            if "nodes" in n:
                traverse(n["nodes"])

    traverse(tree_nodes)
    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[:top_k]


def expand_query(query: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return query
    try:
        prompt = (
            f"Expand this gastroenterology medical query with full terms and synonyms. "
            f"Query: '{query}'. Return ONLY the expanded version."
        )
        response = litellm.completion(
            model=RETRIEVE_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=60,
            api_key=api_key,
        )
        return response.choices[0].message.content.strip() + " " + query
    except Exception:
        return query


def ai_rank_nodes(query: str, candidates: list) -> list:
    if not candidates:
        return []

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return candidates[:6]

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
            model=RETRIEVE_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=40,
            api_key=api_key,
        )
        ans = response.choices[0].message.content.strip().upper()
        if "NONE" in ans:
            return []
        indices = [int(i.strip()) for i in ans.split(",") if i.strip().isdigit()]
        return [candidates[i] for i in indices if i < len(candidates)]
    except Exception:
        return candidates[:6]


def _chunks_from_results(best_results: list, top_k: int) -> List[Dict[str, Any]]:
    chunks: List[Dict[str, Any]] = []
    for res in best_results[:top_k]:
        node = res["node"]
        full_text = node.get("text", "").strip()
        summary = node.get("summary", "").strip()
        content = full_text[:2000] if full_text else summary[:1500]
        chunks.append(
            {
                "source": res["doc_short"],
                "doc_type": res["doc_type"],
                "title": node.get("title", "Unknown Section"),
                "content": content,
                "score": float(res.get("score", 0)),
            }
        )
    return chunks


def format_context(chunks: List[Dict[str, Any]]) -> str:
    blocks = []
    for c in chunks:
        block = (
            f"SOURCE: {c['source']} ({c['doc_type']})\n"
            f"SECTION: {c['title']}\n"
            f"CONTENT:\n{c['content']}\n"
            f"---"
        )
        blocks.append(block)
    return "\n\n".join(blocks)


def retrieve(
    query: str,
    top_k: int = 6,
    use_llm_ranking: bool = True,
) -> Dict[str, Any]:
    """
    Retrieve relevant GI knowledge chunks from indexed PageIndex JSON trees.

    Returns dict with keys: found, chunks, context, expanded_query, candidate_count, selected_count.
    """
    query = (query or "").strip()
    if not query:
        return {
            "found": False,
            "chunks": [],
            "context": None,
            "expanded_query": query,
            "candidate_count": 0,
            "selected_count": 0,
        }

    if use_llm_ranking and not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required when use_llm_ranking=true")

    expanded_q = expand_query(query) if use_llm_ranking else query
    all_candidates: list = []

    for doc_info in DOCUMENTS.values():
        tree_path = doc_info["tree_path"]
        if not tree_path.exists():
            continue
        try:
            data = load_document_structure(str(tree_path))
            doc_candidates = get_candidates(
                expanded_q,
                data.get("structure", []),
                doc_info["short"],
                doc_info["type"],
            )
            all_candidates.extend(doc_candidates)
        except Exception:
            continue

    candidate_count = len(all_candidates)
    all_candidates.sort(key=lambda x: x["score"], reverse=True)

    if use_llm_ranking:
        best_results = ai_rank_nodes(query, all_candidates[:25]) or all_candidates[:top_k]
    else:
        best_results = all_candidates[:top_k]

    chunks = _chunks_from_results(best_results, top_k)
    found = len(chunks) > 0

    return {
        "found": found,
        "chunks": chunks,
        "context": format_context(chunks) if found else None,
        "expanded_query": expanded_q,
        "candidate_count": candidate_count,
        "selected_count": len(chunks),
    }
