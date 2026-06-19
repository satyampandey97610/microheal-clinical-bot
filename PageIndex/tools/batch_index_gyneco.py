"""
GynecoRAG Batch Indexer
========================
Indexes all Gyneco PDFs using gpt-4o-mini ONLY.
Enhanced token tracking: logs tokens even for FAILED PDFs.
Smart ordering: small PDFs first, large textbooks last.

Usage:
    python PageIndex/tools/batch_index_gyneco.py
"""

import os
import sys
import json
import traceback
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Ensure we can import the PageIndex engine
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))

from PageIndex.pageindex.page_index import page_index_main
from PageIndex.pageindex.utils import ConfigLoader, GLOBAL_USAGE

# Directories
PDF_DIR = root_dir / "GynecoRAG" / "data"
RESULTS_DIR = root_dir / "GynecoRAG" / "index"
LOGS_DIR = root_dir / "logs"
TOKEN_LOG_PATH = LOGS_DIR / "token_usage_master.json"

load_dotenv(dotenv_path=root_dir / ".env")

SESSION_START = datetime.now().isoformat()

# ── Smart ordering: small PDFs first, large textbooks last ──
# Based on deep validation results (page counts)
INDEXING_ORDER = [
    "358_20190306183538.pdf",
    "Handbook_of_Obstetrics_Guideline.pdf"
]


def save_token_log(pdf_stem=None, before_usage=None, status="SUCCESS"):
    """
    Update master token log with current usage.
    CRITICAL: Also logs tokens for FAILED PDFs so no usage is lost.
    """
    if TOKEN_LOG_PATH.exists():
        with open(TOKEN_LOG_PATH, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception:
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
            "domain": "GynecoRAG",
            "model": "gpt-4o-mini",
            "pdfs": {},
            "session_totals": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "api_calls": 0,
            },
        }
        data["all_sessions"].append(session)

    # Merge current PDF usage if provided
    if pdf_stem and before_usage:
        pdf_usage = {}
        for k in GLOBAL_USAGE.keys():
            pdf_usage[k] = GLOBAL_USAGE[k] - before_usage[k]
        pdf_usage["status"] = status
        pdf_usage["timestamp"] = datetime.now().isoformat()
        session["pdfs"][pdf_stem] = pdf_usage

    # Recalculate session totals
    session["session_totals"] = {
        "prompt_tokens": sum(p.get("prompt_tokens", 0) for p in session["pdfs"].values()),
        "completion_tokens": sum(p.get("completion_tokens", 0) for p in session["pdfs"].values()),
        "total_tokens": sum(p.get("total_tokens", 0) for p in session["pdfs"].values()),
        "api_calls": sum(p.get("api_calls", 0) for p in session["pdfs"].values()),
    }
    session["session_end"] = datetime.now().isoformat()

    # Recalculate grand total
    grand_total = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "api_calls": 0,
    }
    for s in data["all_sessions"]:
        totals = s.get("session_totals", {})
        for k in list(grand_total.keys()):
            grand_total[k] += totals.get(k, 0)
    grand_total["last_updated"] = datetime.now().isoformat()
    data["grand_total"] = grand_total

    with open(TOKEN_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def main():
    print(f"\n{'='*60}")
    print(f"  GynecoRAG Batch Indexer")
    print(f"  Model: gpt-4o-mini (HARDCODED)")
    print(f"  Session: {SESSION_START}")
    print(f"{'='*60}\n")

    # Ensure index directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Set the global SESSION_START in PageIndex.utils
    import PageIndex.pageindex.utils as pi_utils
    pi_utils.SESSION_START = SESSION_START

    # Build ordered PDF list
    pdfs = []
    for pdf_name in INDEXING_ORDER:
        pdf_path = PDF_DIR / pdf_name
        if pdf_name == "pone.0231939.pdf":
            print(f"[SKIP] Corrupted PDF explicitly skipped: {pdf_name}")
            continue
        if pdf_path.exists():
            pdfs.append(pdf_path)
        else:
            print(f"[WARN] PDF not found, skipping: {pdf_name}")

    # Also pick up any PDFs not in the explicit order (safety net)
    all_pdfs_in_dir = set(p.name for p in PDF_DIR.glob("*.pdf"))
    ordered_names = set(INDEXING_ORDER)
    for extra in sorted(all_pdfs_in_dir - ordered_names):
        if extra == "pone.0231939.pdf":
            continue
        pdfs.append(PDF_DIR / extra)
        print(f"[INFO] Extra PDF found (not in order list): {extra}")

    if not pdfs:
        print(f"[ERROR] No PDFs found in {PDF_DIR}")
        return

    print(f"Found {len(pdfs)} documents to index.\n")

    success, failed, skipped = 0, 0, 0
    failed_pdfs = []

    for idx, pdf_path in enumerate(pdfs, 1):
        stem = pdf_path.stem
        output_file = RESULTS_DIR / f"{stem}_structure.json"

        if output_file.exists():
            print(f"[SKIP] ({idx}/{len(pdfs)}) Already indexed: {pdf_path.name}")
            skipped += 1
            continue

        print(f"\n[INDEXING] ({idx}/{len(pdfs)}) {pdf_path.name}...")

        # Set the current PDF stem for raw JSONL logging
        pi_utils.CURRENT_PDF_STEM = stem

        # Record usage BEFORE this PDF
        before_usage = {k: v for k, v in GLOBAL_USAGE.items()}

        try:
            # Explicitly force gpt-4o-mini — NO premium model
            options = {
                "model": "gpt-4o-mini",
                "if_add_node_id": "yes",
                "if_add_node_summary": "yes",
                "if_add_doc_description": "yes",
                "if_add_node_text": "yes",
            }
            opt = ConfigLoader().load(options)

            result = page_index_main(str(pdf_path), opt)

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            print(f"   Done -> {output_file.name}")
            success += 1

            # Save token logs after every successful file
            save_token_log(stem, before_usage, status="SUCCESS")

        except Exception as e:
            error_msg = str(e)
            tb = traceback.format_exc()
            print(f"   [ERROR] Failed: {error_msg}")
            print(f"   Traceback:\n{tb}")
            failed += 1
            failed_pdfs.append(pdf_path.name)

            # CRITICAL: Log tokens consumed EVEN for failed PDFs
            # This ensures we never lose cost data
            save_token_log(stem, before_usage, status=f"FAILED: {error_msg[:200]}")
            print(f"   [TOKEN LOG] Partial tokens for failed PDF saved to master log")

    # ── Final Summary ──
    print(f"\n{'='*60}")
    print(f"  GynecoRAG Indexing Complete")
    print(f"{'='*60}")
    print(f"  Succeeded: {success}")
    print(f"  Failed:    {failed}")
    print(f"  Skipped:   {skipped}")
    print(f"  Total:     {len(pdfs)}")
    print(f"\n  Token logs: {TOKEN_LOG_PATH}")
    print(f"  Index dir:  {RESULTS_DIR}")

    if failed_pdfs:
        print(f"\n  FAILED PDFs (tokens still logged):")
        for fp in failed_pdfs:
            print(f"    - {fp}")

    # Show today's session token summary
    if TOKEN_LOG_PATH.exists():
        with open(TOKEN_LOG_PATH, "r", encoding="utf-8") as f:
            log_data = json.load(f)
        for s in log_data.get("all_sessions", []):
            if s.get("session_start") == SESSION_START:
                totals = s.get("session_totals", {})
                print(f"\n  TODAY'S SESSION TOKENS:")
                print(f"    Prompt:     {totals.get('prompt_tokens', 0):>10,}")
                print(f"    Completion: {totals.get('completion_tokens', 0):>10,}")
                print(f"    Total:      {totals.get('total_tokens', 0):>10,}")
                print(f"    API Calls:  {totals.get('api_calls', 0):>10,}")
                print(f"\n  PER-PDF BREAKDOWN:")
                for pdf_name, pdf_data in s.get("pdfs", {}).items():
                    status_str = pdf_data.get("status", "unknown")
                    total = pdf_data.get("total_tokens", 0)
                    calls = pdf_data.get("api_calls", 0)
                    print(f"    {pdf_name[:45]:<48s} {total:>8,} tokens | {calls:>3} calls | {status_str}")
                break

    # Cleanup live tracker
    if os.path.exists("live_progress.txt"):
        try:
            os.remove("live_progress.txt")
        except Exception:
            pass


if __name__ == "__main__":
    main()
