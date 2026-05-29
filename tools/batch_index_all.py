import os
import sys
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import litellm
from run_pageindex import page_index_main, ConfigLoader
from pageindex.utils import GLOBAL_USAGE

# Load environment
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

# Registry of documents to index
PDF_METADATA = {
    "I-546_Gastro": {"key": "first_principles", "year": 2012, "type": "textbook"},
    "Yamadas-Handbook-of-Gastroenterology-2019": {"key": "yamada", "year": 2019, "type": "handbook"},
    "EMJ-Gastroenterology-10_1-2021-4": {"key": "emj_journal", "year": 2021, "type": "journal"},
    "PageIndex_Optimized_GI_Report": {"key": "kaggle_dataset", "year": 2024, "type": "dataset"},
    "digestive_datasets_cran": {"key": "cran_datasets", "year": 2024, "type": "dataset"},
    "15Casebook in gastroenterology": {"key": "casebook_gastro", "year": 2015, "type": "casebook"},
    "40264_2023_Article_1392": {"key": "glp1_research_2023", "year": 2023, "type": "journal"},
    "GLP-1s-and-Diet": {"key": "glp1_diet", "year": 2023, "type": "guide"},
    "NutritionalprioritiestosupportGLP-1therapyy": {"key": "glp1_nutrition_priorities", "year": 2024, "type": "guide"},
    "Your_Ultimate_Guide_to_GLP-1_Med": {"key": "glp1_ultimate_guide", "year": 2024, "type": "guide"},
    "e002519.full": {"key": "glp1_clinical_study", "year": 2023, "type": "journal"},
    "fcdhc-06-1720794": {"key": "glp1_frontiers_article", "year": 2023, "type": "journal"},
    "ilide.info-the-ultimate-glp-1-diet-cookbook-for-beginners-2-pr_69c9a251ad17358bf6845824b629ca1e": {"key": "glp1_diet_cookbook", "year": 2024, "type": "guide"},
    "protein-balance-for-glp1s-sample-meal-plan": {"key": "glp1_meal_plan", "year": 2024, "type": "guide"},
}

# Directories
PDF_DIR = Path(__file__).parent / "pdfs"
RESULTS_DIR = Path(__file__).parent / "results"
LOGS_DIR = Path(__file__).parent / "logs"
TOKEN_LOG_PATH = LOGS_DIR / "token_usage_master.json"

LOGS_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

def save_token_log():
    """Update master token log with current usage."""
    usage = {
        "timestamp": datetime.now().isoformat(),
        "usage": GLOBAL_USAGE
    }
    with open(TOKEN_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(usage, f, indent=2)

def main():
    """Batch index all PDFs in the pdfs directory."""
    pdfs = sorted(PDF_DIR.glob("*.pdf"))
    success, failed = 0, 0

    print(f"--- GastroRAG Batch Indexer ---")
    print(f"Found {len(pdfs)} documents in {PDF_DIR}\n")

    for pdf_path in pdfs:
        stem = pdf_path.stem
        output_file = RESULTS_DIR / f"{stem}_structure.json"

        if output_file.exists():
            print(f"[SKIP] Already indexed: {pdf_path.name}")
            continue

        print(f"[INDEXING] {pdf_path.name}...")
        try:
            options = {
                'model': 'gpt-4o-mini',
                'if_add_node_id': 'yes',
                'if_add_node_summary': 'yes',
                'if_add_doc_description': 'yes',
                'if_add_node_text': 'yes',
            }
            opt = ConfigLoader().load(options)
            result = page_index_main(str(pdf_path), opt)

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print(f"   Done -> {output_file.name}")
            success += 1
            save_token_log()
        except Exception as e:
            print(f"   [ERROR] Failed: {e}")
            failed += 1

    print(f"\n--- Process Complete ---")
    print(f"Succeeded: {success} | Failed: {failed}")
    print(f"Token log: {TOKEN_LOG_PATH}")

if __name__ == "__main__":
    main()
re saved to: {output_file}')
            success_count += 1

            # Save token log and update registry after each PDF for visibility
            sync_usage_to_session()
            grand_total = save_master_token_log()
            update_gastro_agent_tool()
            
        except Exception as e:
            print(f"[ERROR] FAILED: {pdf_path.name} -> {e}")
            fail_count += 1

    # Final summary print
    if success_count > 0 or fail_count > 0:
        if 'grand_total' in locals():
            print_token_summary(grand_total)
    
    print(f"\n[DONE] Batch indexing complete - {success_count} succeeded, {fail_count} failed")
    print(f"   Token log : {TOKEN_LOG_PATH}")
    print(f"   Results   : {RESULTS_DIR}")
