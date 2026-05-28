"""
GastroRAG Agent — Gastroenterology Specialist
==============================================
Lightweight wrapper around the ClinicalEngine for backward compatibility.
Can be imported directly by WhatsApp bots, workflows, or any integration.

Usage:
    from GastroRAG.gastro_agent import query_gastro
    result = query_gastro("What causes GERD?")
"""

import json
import os
import glob
from pathlib import Path


# ──────────────────────────────────────────────────────────────────
#  Dynamic Registry Loader
# ──────────────────────────────────────────────────────────────────

AGENT_DIR = Path(__file__).parent
INDEX_DIR = AGENT_DIR / "index"
DATA_DIR = AGENT_DIR / "data"


def load_gastro_documents() -> dict:
    """Dynamically scan and register all Gastro index JSON files."""
    registry = {}
    if not INDEX_DIR.exists():
        return registry

    for file in glob.glob(str(INDEX_DIR / "*_structure.json")):
        p = Path(file)
        doc_key = p.name.replace("_structure.json", "")
        short_name = doc_key.replace("-", " ").replace("_", " ").title()
        if len(short_name) > 45:
            short_name = short_name[:42] + "..."

        doc_type = "Reference"
        key_lower = doc_key.lower()
        if "journal" in key_lower or "article" in key_lower:
            doc_type = "Journal"
        elif "dataset" in key_lower:
            doc_type = "Dataset"
        elif "book" in key_lower or "casebook" in key_lower:
            doc_type = "Textbook"
        elif "guide" in key_lower or "diet" in key_lower or "meal" in key_lower:
            doc_type = "Guide"

        registry[doc_key] = {
            "tree_path": p,
            "short": short_name,
            "type": doc_type,
        }

    return registry


DOCUMENTS = load_gastro_documents()


# ──────────────────────────────────────────────────────────────────
#  Core Retrieval Logic
# ──────────────────────────────────────────────────────────────────

def search_tree_structure(tree: list, query: str) -> list:
    """Keyword-based search in the document hierarchy."""
    query_lower = query.lower()
    keywords = [w for w in query_lower.split() if len(w) > 2]
    relevant_nodes = []

    def search_nodes(nodes):
        for node in nodes:
            title = (node.get("title") or "").lower()
            summary = (node.get("summary") or "").lower()
            content = (node.get("text") or node.get("content") or "").lower()
            text = title + " " + summary + " " + content

            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                relevant_nodes.append({"node": node, "score": score})

            if "nodes" in node:
                search_nodes(node["nodes"])

    search_nodes(tree)
    relevant_nodes.sort(key=lambda x: x["score"], reverse=True)
    return [item["node"] for item in relevant_nodes[:5]]


def gastro_knowledge_tool(query: str, source_filter: str = None) -> str:
    """Query the GastroRAG Knowledge Base and return structured context string."""
    results = []
    docs_to_search = {
        k: v for k, v in DOCUMENTS.items()
        if source_filter is None or k == source_filter
    }

    for doc_key, doc_info in docs_to_search.items():
        tree_path = doc_info["tree_path"]
        if not tree_path.exists():
            continue

        try:
            with open(tree_path, encoding="utf-8") as f:
                tree_data = json.load(f)

            structure = tree_data.get("structure", tree_data)
            if not isinstance(structure, list):
                continue

            relevant_nodes = search_tree_structure(structure, query)

            if relevant_nodes:
                sections = [n.get("title", "Unknown") for n in relevant_nodes[:3]]
                content_parts = []
                for node in relevant_nodes:
                    text = node.get("text") or node.get("content") or node.get("summary") or ""
                    if text:
                        content_parts.append(f"[{node.get('title', 'Section')}]\n{text[:1200]}")

                results.append({
                    "source_label": doc_info["short"],
                    "type": doc_info["type"],
                    "sections": sections,
                    "content": "\n\n".join(content_parts),
                })

        except Exception as e:
            print(f"Error querying {doc_key}: {e}")
            continue

    if not results:
        return "NO_RESULTS: No relevant gastroenterology information found."

    context_blocks = []
    for r in results:
        block = (
            f"SOURCE: {r['source_label']}\n"
            f"TYPE: {r['type'].upper()}\n"
            f"SECTIONS: {' | '.join(r['sections'])}\n"
            f"CONTENT:\n{r['content']}\n"
            f"---"
        )
        context_blocks.append(block)

    return "\n\n".join(context_blocks)


# ──────────────────────────────────────────────────────────────────
#  High-Level Query Function (for WhatsApp bot / workflow use)
# ──────────────────────────────────────────────────────────────────

def query_gastro(question: str, history: list = None) -> dict:
    """
    Query the Gastro specialist. Returns structured result dict.
    This is a convenience wrapper — for full power, use ClinicalEngine.

    Returns:
        {"answer": str, "sources": list, "domain": "Gastroenterology", "out_of_domain": bool}
    """
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from clinical_engine import ClinicalEngine
    engine = ClinicalEngine("gastro")
    return engine.query(question, history)


# ──────────────────────────────────────────────────────────────────
#  Standalone Test
# ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"GastroRAG Agent — Loaded {len(DOCUMENTS)} indexed documents")
    print(f"Index directory: {INDEX_DIR}")
    print()

    test_query = "What is the treatment for Helicobacter pylori infection?"
    print(f"Testing: {test_query}\n")
    result = gastro_knowledge_tool(test_query)
    print(result[:2000])
