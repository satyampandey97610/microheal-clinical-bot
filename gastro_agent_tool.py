import json
import os
from pathlib import Path
import sys
import PyPDF2

# Add current directory to path for imports
sys.path.append('.')

# Document Knowledge Base Registry
DOCUMENTS = {
    "casebook_gastro": {
        "tree_path": "./results/15Casebook in gastroenterology_structure.json",
        "pdf_path":  "./pdfs/15Casebook in gastroenterology.pdf",
        "description": "Casebook in Gastroenterology — Clinical case-based learning resource",
        "year": 2015,
        "type": "casebook"
    },
    "glp1_research_2023": {
        "tree_path": "./results/40264_2023_Article_1392_structure.json",
        "pdf_path":  "./pdfs/40264_2023_Article_1392.pdf",
        "description": "GLP-1 Research Article (2023) — Peer-reviewed study on therapy outcomes",
        "year": 2023,
        "type": "journal"
    },
    "cran_datasets": {
        "tree_path": "./results/digestive_datasets_cran_structure.json",
        "pdf_path":  "./pdfs/digestive_datasets_cran.pdf",
        "description": "DigestiveDataSets CRAN — 25 curated clinical research datasets",
        "year": 2024,
        "type": "dataset"
    },
    "glp1_clinical_study": {
        "tree_path": "./results/e002519.full_structure.json",
        "pdf_path":  "./pdfs/e002519.full.pdf",
        "description": "GLP-1 Clinical Study (e002519) — Clinical trial outcomes",
        "year": 2023,
        "type": "journal"
    },
    "emj_journal": {
        "tree_path": "./results/EMJ-Gastroenterology-10_1-2021-4_structure.json",
        "pdf_path":  "./pdfs/EMJ-Gastroenterology-10_1-2021-4.pdf",
        "description": "EMJ Gastroenterology Vol.10.1 (2021) — Clinical research journal",
        "year": 2021,
        "type": "journal"
    },
    "glp1_frontiers_article": {
        "tree_path": "./results/fcdhc-06-1720794_structure.json",
        "pdf_path":  "./pdfs/fcdhc-06-1720794.pdf",
        "description": "Frontiers in Clinical Diabetes — GLP-1 therapy mechanisms",
        "year": 2023,
        "type": "journal"
    },
    "glp1_diet": {
        "tree_path": "./results/GLP-1s-and-Diet_structure.json",
        "pdf_path":  "./pdfs/GLP-1s-and-Diet.pdf",
        "description": "GLP-1s and Diet — Clinical guide on nutritional strategies",
        "year": 2023,
        "type": "guide"
    },
    "first_principles": {
        "tree_path": "./results/I-546_Gastro_structure.json",
        "pdf_path":  "./pdfs/I-546_Gastro.pdf",
        "description": "First Principles of Gastroenterology & Hepatology — Academic textbook",
        "year": 2012,
        "type": "textbook"
    },
    "glp1_diet_cookbook": {
        "tree_path": "./results/ilide.info-the-ultimate-glp-1-diet-cookbook-for-beginners-2-pr_69c9a251ad17358bf6845824b629ca1e_structure.json",
        "pdf_path":  "./pdfs/ilide.info-the-ultimate-glp-1-diet-cookbook-for-beginners-2-pr_69c9a251ad17358bf6845824b629ca1e.pdf",
        "description": "The Ultimate GLP-1 Diet Cookbook — Practical meal planning",
        "year": 2024,
        "type": "guide"
    },
    "glp1_nutrition_priorities": {
        "tree_path": "./results/NutritionalprioritiestosupportGLP-1therapyy_structure.json",
        "pdf_path":  "./pdfs/NutritionalprioritiestosupportGLP-1therapyy.pdf",
        "description": "Nutritional Priorities for GLP-1 Therapy — Evidence-based framework",
        "year": 2024,
        "type": "guide"
    },
    "kaggle_dataset": {
        "tree_path": "./results/PageIndex_Optimized_GI_Report_structure.json",
        "pdf_path":  "./pdfs/PageIndex_Optimized_GI_Report.pdf",
        "description": "GI Disease Clinical Dataset — 30,560 patient records",
        "year": 2024,
        "type": "dataset"
    },
    "glp1_meal_plan": {
        "tree_path": "./results/protein-balance-for-glp1s-sample-meal-plan_structure.json",
        "pdf_path":  "./pdfs/protein-balance-for-glp1s-sample-meal-plan.pdf",
        "description": "Protein Balance Sample Meal Plan — Structured guide",
        "year": 2024,
        "type": "guide"
    },
    "yamada": {
        "tree_path": "./results/Yamadas-Handbook-of-Gastroenterology-2019_structure.json",
        "pdf_path":  "./pdfs/Yamadas-Handbook-of-Gastroenterology-2019.pdf",
        "description": "Yamada's Handbook of Gastroenterology (2019) — Clinical point-of-care reference",
        "year": 2019,
        "type": "handbook"
    },
    "glp1_ultimate_guide": {
        "tree_path": "./results/Your_Ultimate_Guide_to_GLP-1_Med_structure.json",
        "pdf_path":  "./pdfs/Your_Ultimate_Guide_to_GLP-1_Med.pdf",
        "description": "Your Ultimate Guide to GLP-1 Medications — Comprehensive reference",
        "year": 2024,
        "type": "guide"
    }
}

# --- Core Logic ---

def gastro_knowledge_tool(query: str, source_filter: str = None) -> str:
    """Query the GastroRAG Knowledge Base and return structured context."""
    results = []
    docs_to_search = {
        k: v for k, v in DOCUMENTS.items()
        if source_filter is None or k == source_filter
    }

    for doc_key, doc_info in docs_to_search.items():
        tree_path = Path(doc_info["tree_path"])
        pdf_path = Path(doc_info["pdf_path"])

        if not tree_path.exists() or not pdf_path.exists():
            continue

        try:
            with open(tree_path) as f:
                tree_data = json.load(f)

            tree = tree_data.get("structure", [])
            relevant_nodes = search_tree_structure(tree, query)

            if relevant_nodes:
                content = extract_content_from_nodes(relevant_nodes, pdf_path)
                results.append({
                    "source_label": doc_info["description"],
                    "year": doc_info["year"],
                    "type": doc_info["type"],
                    "sections": [n.get("title", "Unknown") for n in relevant_nodes[:3]],
                    "content": content
                })

        except Exception as e:
            print(f"Error querying {doc_key}: {e}")
            continue

    if not results:
        return "NO_RESULTS: No relevant clinical information found."

    context_blocks = []
    for r in results:
        year_note = f" [{r['year']}]"
        block = (
            f"SOURCE: {r['source_label']}{year_note}\n"
            f"TYPE: {r['type'].upper()}\n"
            f"SECTIONS: {' | '.join(r['sections'])}\n"
            f"CONTENT:\n{r['content']}\n"
            f"---"
        )
        context_blocks.append(block)

    return "\n\n".join(context_blocks)

def search_tree_structure(tree: list, query: str) -> list:
    """Simple keyword-based search in the document hierarchy."""
    query_lower = query.lower()
    keywords = query_lower.split()
    relevant_nodes = []

    def search_nodes(nodes):
        for node in nodes:
            title = node.get("title", "").lower()
            summary = node.get("summary", "").lower()
            text = title + " " + summary
            
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                relevant_nodes.append({"node": node, "score": score})

            if "nodes" in node:
                search_nodes(node["nodes"])

    search_nodes(tree)
    relevant_nodes.sort(key=lambda x: x["score"], reverse=True)
    return [item["node"] for item in relevant_nodes[:5]]

def extract_content_from_nodes(nodes: list, pdf_path: Path) -> str:
    """Extract text content from specific PDF pages defined in nodes."""
    try:
        content_parts = []
        page_indices = set()
        
        for node in nodes:
            if "start_index" in node: page_indices.add(node["start_index"])
            if "end_index" in node: page_indices.add(node["end_index"])
        
        with open(pdf_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page_idx in sorted(page_indices):
                if 0 <= page_idx < len(pdf_reader.pages):
                    text = pdf_reader.pages[page_idx].extract_text()
                    if text:
                        content_parts.append(f"[Page {page_idx + 1}]\n{text[:1200]}")
        
        return "\n\n".join(content_parts) if content_parts else "Content extraction failed."
    except Exception as e:
        return f"Extraction Error: {str(e)}"

if __name__ == "__main__":
    test_query = "Helicobacter pylori treatment"
    print(f"Testing GastroRAG Tool: {test_query}\n")
    print(gastro_knowledge_tool(test_query)[:1000])terology knowledge base."""
#     return gastro_knowledge_tool(query)

# ── Standalone test ─────────────────────────────────────────────
if __name__ == "__main__":
    test_query = "What is the treatment for Helicobacter pylori infection?"
    print(f"Testing query: {test_query}\n")
    result = gastro_knowledge_tool(test_query)
    print(result[:2000])  # Print first 2000 chars for preview
