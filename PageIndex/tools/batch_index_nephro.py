import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Ensure we can import the PageIndex engine
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))

from PageIndex.pageindex.page_index import page_index_main
from PageIndex.pageindex.utils import ConfigLoader, GLOBAL_USAGE

# Directories
PDF_DIR = root_dir / "NephroRAG" / "data"
RESULTS_DIR = root_dir / "NephroRAG" / "index"
LOGS_DIR = root_dir / "logs"
TOKEN_LOG_PATH = LOGS_DIR / "token_usage_master.json"

load_dotenv(dotenv_path=root_dir / ".env")

SESSION_START = datetime.now().isoformat()

def save_token_log(pdf_stem=None, before_usage=None):
    """Update master token log with current usage."""
    if TOKEN_LOG_PATH.exists():
        with open(TOKEN_LOG_PATH, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except:
                data = {"all_sessions": []}
    else:
        data = {"all_sessions": []}
        LOGS_DIR.mkdir(exist_ok=True)
    
    if "all_sessions" not in data:
        data["all_sessions"] = []

    # Find or create current session
    session = None
    for s in data["all_sessions"]:
        if s.get("session_start") == SESSION_START:
            session = s
            break
    if not session:
        session = {
            "session_start": SESSION_START,
            "session_end": datetime.now().isoformat(),
            "pdfs": {},
            "session_totals": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "api_calls": 0
            }
        }
        data["all_sessions"].append(session)

    # Merge current PDF usage if provided
    if pdf_stem and before_usage:
        pdf_usage = {}
        for k in GLOBAL_USAGE.keys():
            pdf_usage[k] = GLOBAL_USAGE[k] - before_usage[k]
        session["pdfs"][pdf_stem] = pdf_usage

    # Recalculate session totals
    session["session_totals"] = {
        "prompt_tokens": sum(p.get("prompt_tokens", 0) for p in session["pdfs"].values()),
        "completion_tokens": sum(p.get("completion_tokens", 0) for p in session["pdfs"].values()),
        "total_tokens": sum(p.get("total_tokens", 0) for p in session["pdfs"].values()),
        "api_calls": sum(p.get("api_calls", 0) for p in session["pdfs"].values())
    }
    session["session_end"] = datetime.now().isoformat()

    # Recalculate grand total
    grand_total = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "api_calls": 0
    }
    for s in data["all_sessions"]:
        totals = s.get("session_totals", {})
        for k in grand_total.keys():
            grand_total[k] += totals.get(k, 0)
    grand_total["last_updated"] = datetime.now().isoformat()
    data["grand_total"] = grand_total

    with open(TOKEN_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def main():
    print(f"\n--- NephroRAG Batch Indexer ---")
    
    # Ensure index directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Find all PDFs
    pdfs = list(PDF_DIR.glob("*.pdf"))
    
    if not pdfs:
        print(f"[ERROR] No PDFs found in {PDF_DIR}")
        return

    print(f"Found {len(pdfs)} documents to index.\n")
    
    success, failed = 0, 0

    for pdf_path in pdfs:
        stem = pdf_path.stem
        output_file = RESULTS_DIR / f"{stem}_structure.json"

        if output_file.exists():
            print(f"[SKIP] Already indexed: {pdf_path.name}")
            continue

        print(f"[INDEXING] {pdf_path.name}...")
        try:
            # Record usage before this PDF
            before_usage = {k: v for k, v in GLOBAL_USAGE.items()}
            
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
            
            # Save token logs after every file so we don't lose data
            save_token_log(stem, before_usage)
            
        except Exception as e:
            print(f"   [ERROR] Failed: {e}")
            failed += 1

    print(f"\n--- Indexing Complete ---")
    print(f"Succeeded: {success} | Failed: {failed}")
    print(f"Total token logs saved to: {TOKEN_LOG_PATH}")

    # Cleanup live tracker
    if os.path.exists("live_progress.txt"):
        try:
            os.remove("live_progress.txt")
        except:
            pass

if __name__ == "__main__":
    main()
