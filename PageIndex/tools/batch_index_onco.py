"""
OncoRAG Batch Indexer — Production-Grade
==========================================
Model        : gpt-4o-mini ONLY (hardcoded, minimum cost)
Cost tracking: TRIPLE-LAYER (raw JSONL + master JSON + markdown report)
Progress     : Live console output at every step
Tokens       : Logged for EVERY PDF — success AND failed — NEVER lost
Pre-flight   : Full integrity check before first API call

Usage (from Medical RAG/):
    python PageIndex/tools/batch_index_onco.py

Run pre-flight first:
    python PageIndex/tools/preflight_onco.py
"""

import os
import sys
import json
import traceback
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# ── Paths ─────────────────────────────────────────────────────────────────────
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

# ── Directories ───────────────────────────────────────────────────────────────
PDF_DIR          = root_dir / "OncoRAG" / "data"
RESULTS_DIR      = root_dir / "OncoRAG" / "index"
LOGS_DIR         = root_dir / "logs"
TOKEN_LOG_PATH   = LOGS_DIR / "token_usage_master.json"
COST_REPORT_PATH = LOGS_DIR / "onco_cost_report.md"

load_dotenv(dotenv_path=root_dir / ".env")
SESSION_START = datetime.now().isoformat()

# ── gpt-4o-mini pricing ───────────────────────────────────────────────────────
PRICE_INPUT_PER_M  = 0.150   # $0.150 per 1M input tokens
PRICE_OUTPUT_PER_M = 0.600   # $0.600 per 1M output tokens

# ── Verified Smart Order (small → large, from pre-analysis) ───────────────────
# Source: PageIndex/tools/analyze_onco_pdfs.py (zero-cost pre-analysis run)
# Format: (filename, verified_pages, doc_type)
INDEXING_ORDER = [
    ("Dtsch_Arztebl_Int-120_445.pdf",           2,    "journal"),
    ("aids-37-1871.pdf",                          12,   "journal"),
    ("dmm-16-050175.pdf",                         15,   "research"),
    ("tbad017.pdf",                               17,   "journal"),
    ("WHO-MHP-HPS-EML-2023.02-eng.pdf",          71,   "who_ref"),
    ("Padova_lectures_vers3.pdf",                 123,  "lectures"),   # heavy front matter
    ("ProstateBook2.pdf",                         184,  "textbook"),
    ("22.-Textbook-of-Medical-Oncology-Fourth-Edition-Cavalli-Textbook-of-Medical-Oncology-PDFDrive-.pdf",
     476, "textbook"),
    ("Oxford-Handbook-of-Oncology-4th-Ed.pdf",   897,  "handbook"),
    ("The MD Anderson Manual of Medical Oncology 3e.pdf", 1274, "manual"),
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def log(msg: str):
    """Timestamped console print — always visible."""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def calc_cost(prompt_tokens: int, completion_tokens: int) -> float:
    """Return USD cost for gpt-4o-mini."""
    return (prompt_tokens / 1_000_000) * PRICE_INPUT_PER_M \
         + (completion_tokens / 1_000_000) * PRICE_OUTPUT_PER_M


# ── Pre-flight check (inline, zero-cost) ─────────────────────────────────────

def run_preflight() -> bool:
    """
    Verifies every PDF is readable with PyPDF2 AND PyMuPDF before any
    API call is made. Returns True if safe to proceed, False otherwise.
    """
    import PyPDF2
    import pymupdf

    log("=" * 62)
    log("  INLINE PRE-FLIGHT CHECK (zero cost)")
    log("=" * 62)

    errors   = []
    warnings = []

    # API key
    api_key = os.getenv("OPENAI_API_KEY", "")
    if api_key and api_key.startswith("sk-"):
        log(f"  API KEY   : OK ({api_key[:14]}...)")
    else:
        errors.append("OPENAI_API_KEY missing or invalid")
        log("  API KEY   : FAIL — key missing or invalid")

    # Directories
    for d, label in [(PDF_DIR, "OncoRAG/data"), (LOGS_DIR, "logs")]:
        if d.exists():
            log(f"  DIR {label:14s}: OK")
        else:
            errors.append(f"Directory missing: {d}")
            log(f"  DIR {label:14s}: FAIL — {d}")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    log(f"  DIR index      : OK (created/verified)")

    # PDFs
    log(f"\n  PDF INTEGRITY CHECK ({len(INDEXING_ORDER)} files):")
    all_pdfs_ok = True
    for fname, exp_pages, doc_type in INDEXING_ORDER:
        p = PDF_DIR / fname
        if not p.exists():
            log(f"    FAIL  MISSING: {fname}")
            errors.append(f"PDF missing: {fname}")
            all_pdfs_ok = False
            continue

        size_mb = p.stat().st_size / (1024 * 1024)
        pdf_issues = []

        # PyPDF2
        try:
            reader = PyPDF2.PdfReader(str(p))
            pypdf2_pages = len(reader.pages)
            if pypdf2_pages == 0:
                pdf_issues.append("0 pages (PyPDF2)")
            # Verify first and last page extract without crash
            _ = reader.pages[0].extract_text()
            if pypdf2_pages > 1:
                _ = reader.pages[-1].extract_text()
        except Exception as e:
            pdf_issues.append(f"PyPDF2: {e}")
            pypdf2_pages = 0

        # PyMuPDF
        try:
            doc = pymupdf.open(str(p))
            mupdf_pages = len(doc)
            doc.close()
            if mupdf_pages == 0:
                pdf_issues.append("0 pages (MuPDF)")
        except Exception as e:
            pdf_issues.append(f"MuPDF: {e}")
            mupdf_pages = 0

        short = fname[:50]
        if pdf_issues:
            for issue in pdf_issues:
                log(f"    WARN  {short}: {issue}")
            warnings.extend(pdf_issues)
        else:
            log(f"    OK    {short}")
            log(f"          {pypdf2_pages}p PyPDF2 | {mupdf_pages}p MuPDF | {size_mb:.1f} MB")

    log("")
    if errors:
        log("  PRE-FLIGHT: ABORT — errors must be fixed first:")
        for e in errors:
            log(f"    - {e}")
        return False
    elif warnings:
        log(f"  PRE-FLIGHT: PROCEED WITH CAUTION ({len(warnings)} warning(s))")
    else:
        log("  PRE-FLIGHT: ALL CLEAR")
    return True


# ── Token log (append-safe, preserves all history) ───────────────────────────

def save_token_log(GLOBAL_USAGE, pdf_stem=None, before_usage=None, status="SUCCESS"):
    """
    Persist token usage to token_usage_master.json.
    - Creates the file if it does not exist.
    - Appends to existing sessions — all history preserved.
    - Logs tokens even for FAILED PDFs (cost data is NEVER lost).
    - Includes USD cost estimate per PDF and session total.
    """
    # Load existing
    if TOKEN_LOG_PATH.exists():
        try:
            with open(TOKEN_LOG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {"all_sessions": []}
    else:
        data = {"all_sessions": []}
        LOGS_DIR.mkdir(exist_ok=True)

    if "all_sessions" not in data:
        data["all_sessions"] = []

    # Find or create current session entry
    session = None
    for s in data["all_sessions"]:
        if s.get("session_start") == SESSION_START:
            session = s
            break
    if not session:
        session = {
            "session_start":  SESSION_START,
            "session_end":    datetime.now().isoformat(),
            "domain":         "OncoRAG",
            "model":          "gpt-4o-mini",
            "pdfs":           {},
            "session_totals": {
                "prompt_tokens":      0,
                "completion_tokens":  0,
                "total_tokens":       0,
                "api_calls":          0,
                "estimated_cost_usd": 0.0,
            },
        }
        data["all_sessions"].append(session)

    # Compute delta for this PDF
    if pdf_stem and before_usage:
        delta = {k: GLOBAL_USAGE[k] - before_usage[k] for k in GLOBAL_USAGE}
        delta["status"]            = status
        delta["timestamp"]         = datetime.now().isoformat()
        delta["estimated_cost_usd"] = round(
            calc_cost(delta.get("prompt_tokens", 0), delta.get("completion_tokens", 0)), 6
        )
        session["pdfs"][pdf_stem] = delta

    # Recalculate session totals
    pt = sum(p.get("prompt_tokens", 0) for p in session["pdfs"].values())
    ct = sum(p.get("completion_tokens", 0) for p in session["pdfs"].values())
    session["session_totals"] = {
        "prompt_tokens":      pt,
        "completion_tokens":  ct,
        "total_tokens":       sum(p.get("total_tokens", 0) for p in session["pdfs"].values()),
        "api_calls":          sum(p.get("api_calls", 0) for p in session["pdfs"].values()),
        "estimated_cost_usd": round(calc_cost(pt, ct), 6),
    }
    session["session_end"] = datetime.now().isoformat()

    # Recalculate grand total across ALL sessions and ALL departments
    grand = {
        "prompt_tokens": 0, "completion_tokens": 0,
        "total_tokens": 0,  "api_calls": 0,
        "estimated_cost_usd": 0.0,
    }
    for s in data["all_sessions"]:
        t = s.get("session_totals", {})
        for k in ["prompt_tokens", "completion_tokens", "total_tokens", "api_calls"]:
            grand[k] += t.get(k, 0)
        grand["estimated_cost_usd"] += t.get("estimated_cost_usd", 0.0)
    grand["estimated_cost_usd"] = round(grand["estimated_cost_usd"], 6)
    grand["last_updated"] = datetime.now().isoformat()
    data["grand_total"] = grand

    # Atomic write
    with open(TOKEN_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# ── Markdown cost report ──────────────────────────────────────────────────────

def write_cost_report(session_data: dict, failed_pdfs: list):
    """Write a clean human-readable cost report in Markdown."""
    pdfs   = session_data.get("pdfs", {})
    totals = session_data.get("session_totals", {})

    # Page reference from pre-analysis
    page_ref = {
        "Dtsch_Arztebl_Int-120_445": 2,
        "aids-37-1871": 12,
        "dmm-16-050175": 15,
        "tbad017": 17,
        "WHO-MHP-HPS-EML-2023.02-eng": 71,
        "Padova_lectures_vers3": 123,
        "ProstateBook2": 184,
        "22.-Textbook-of-Medical-Oncology-Fourth-Edition-Cavalli-Textbook-of-Medical-Oncology-PDFDrive-": 476,
        "Oxford-Handbook-of-Oncology-4th-Ed": 897,
        "The MD Anderson Manual of Medical Oncology 3e": 1274,
    }

    lines = [
        "# OncoRAG Indexing Cost Report",
        "",
        f"**Session start** : `{SESSION_START}`",
        f"**Completed**     : `{datetime.now().isoformat()}`",
        f"**Model**         : gpt-4o-mini (hardcoded)",
        f"**Pricing**       : Input ${PRICE_INPUT_PER_M}/1M | Output ${PRICE_OUTPUT_PER_M}/1M",
        "",
        "---",
        "## Per-PDF Cost Breakdown",
        "",
        "| PDF | Pages | Prompt Tok | Compl Tok | Total Tok | API Calls | Cost USD | Status |",
        "| :--- | ---: | ---: | ---: | ---: | ---: | ---: | :--- |",
    ]

    session_cost = 0.0
    for stem, u in pdfs.items():
        pages  = page_ref.get(stem, "?")
        pt     = u.get("prompt_tokens", 0)
        ct     = u.get("completion_tokens", 0)
        tt     = u.get("total_tokens", 0)
        calls  = u.get("api_calls", 0)
        cost   = u.get("estimated_cost_usd", round(calc_cost(pt, ct), 6))
        status = u.get("status", "UNKNOWN")
        session_cost += cost
        short  = stem[:45] + "..." if len(stem) > 45 else stem
        lines.append(
            f"| {short} | {pages} | {pt:,} | {ct:,} | {tt:,} | {calls} | ${cost:.4f} | {status} |"
        )

    lines += [
        "",
        "---",
        "## Session Totals",
        "",
        "| Metric | Value |",
        "| :--- | ---: |",
        f"| Prompt Tokens     | {totals.get('prompt_tokens', 0):,} |",
        f"| Completion Tokens | {totals.get('completion_tokens', 0):,} |",
        f"| Total Tokens      | {totals.get('total_tokens', 0):,} |",
        f"| API Calls         | {totals.get('api_calls', 0):,} |",
        f"| **Estimated Cost**| **${totals.get('estimated_cost_usd', 0.0):.4f} USD** |",
        "",
    ]

    if failed_pdfs:
        lines += [
            "## Failed PDFs (tokens still tracked)",
            "",
        ]
        for fp in failed_pdfs:
            lines.append(f"- `{fp}`")
        lines.append("")

    lines += [
        "---",
        "## Log Files",
        f"- Master (JSON) : `logs/token_usage_master.json`",
        f"- Raw per-call  : `logs/token_usage_raw.jsonl`",
        f"- This report   : `logs/onco_cost_report.md`",
    ]

    with open(COST_REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    log(f"  Cost report written: {COST_REPORT_PATH.name}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    log("=" * 62)
    log("  OncoRAG Batch Indexer - Production Grade")
    log(f"  Session : {SESSION_START}")
    log(f"  Model   : gpt-4o-mini (HARDCODED - NO premium model)")
    log(f"  Pricing : Input ${PRICE_INPUT_PER_M}/1M | Output ${PRICE_OUTPUT_PER_M}/1M")
    log("=" * 62)

    # ── STEP 1: Inline pre-flight (zero cost) ─────────────────────────────────
    if not run_preflight():
        log("ABORT: Pre-flight failed. Fix errors and re-run.")
        sys.exit(1)

    # ── STEP 2: Import engine (after env is loaded) ───────────────────────────
    log("")
    log("Importing PageIndex engine...")
    try:
        from PageIndex.pageindex.page_index import page_index_main
        from PageIndex.pageindex.utils import ConfigLoader, GLOBAL_USAGE
        import PageIndex.pageindex.utils as pi_utils
        log("  Engine imported OK")
    except Exception as e:
        log(f"  FATAL: Engine import failed: {e}")
        log(traceback.format_exc())
        sys.exit(1)

    # Inject session into PageIndex utils for real-time JSONL logging
    pi_utils.SESSION_START    = SESSION_START
    pi_utils.CURRENT_PDF_STEM = "unknown"

    # ── STEP 3: Build ordered PDF list ────────────────────────────────────────
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    pdfs = []
    missing = []

    for fname, exp_pages, doc_type in INDEXING_ORDER:
        p = PDF_DIR / fname
        if p.exists():
            pdfs.append((p, exp_pages, doc_type))
        else:
            missing.append(fname)
            log(f"  WARN: PDF not found (will skip): {fname}")

    # Safety net: pick up any extra PDFs not in INDEXING_ORDER
    ordered_names = {fname for fname, _, _ in INDEXING_ORDER}
    for extra in sorted(p.name for p in PDF_DIR.glob("*.pdf")):
        if extra not in ordered_names:
            pdfs.append((PDF_DIR / extra, 0, "extra"))
            log(f"  INFO: Extra PDF found (appended): {extra}")

    total = len(pdfs)
    if total == 0:
        log("ABORT: No PDFs found to index.")
        sys.exit(1)

    log("")
    log(f"PDFs to process: {total} | Already-indexed will be skipped.")
    log("")

    # ── STEP 4: Indexing loop ─────────────────────────────────────────────────
    success = 0
    failed  = 0
    skipped = 0
    failed_pdfs = []
    session_running_cost = 0.0

    for idx, (pdf_path, exp_pages, doc_type) in enumerate(pdfs, 1):
        stem        = pdf_path.stem
        output_file = RESULTS_DIR / f"{stem}_structure.json"
        size_mb     = pdf_path.stat().st_size / (1024 * 1024)

        log("-" * 62)
        log(f"[{idx}/{total}] {pdf_path.name}")
        log(f"  Type   : {doc_type} | Pages (expected): {exp_pages} | Size: {size_mb:.1f} MB")

        # Skip already indexed
        if output_file.exists():
            out_kb = output_file.stat().st_size / 1024
            log(f"  STATUS : SKIP (already indexed, {out_kb:.0f} KB)")
            skipped += 1
            continue

        # Set PDF context for real-time JSONL logging
        pi_utils.CURRENT_PDF_STEM = stem

        # Snapshot BEFORE — for delta calculation
        before_usage = {k: v for k, v in GLOBAL_USAGE.items()}
        t_start = time.time()

        log(f"  STATUS : INDEXING... (this may take several minutes)")

        try:
            options = {
                "model":                  "gpt-4o-mini",   # HARDCODED
                "if_add_node_id":         "yes",
                "if_add_node_summary":    "yes",
                "if_add_doc_description": "yes",
                "if_add_node_text":       "yes",
            }
            opt = ConfigLoader().load(options)
            result = page_index_main(str(pdf_path), opt)

            # Write output JSON
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            # Cost delta
            elapsed    = time.time() - t_start
            pt_delta   = GLOBAL_USAGE["prompt_tokens"]    - before_usage["prompt_tokens"]
            ct_delta   = GLOBAL_USAGE["completion_tokens"]- before_usage["completion_tokens"]
            tt_delta   = GLOBAL_USAGE["total_tokens"]     - before_usage["total_tokens"]
            calls_delta= GLOBAL_USAGE["api_calls"]        - before_usage["api_calls"]
            cost_this  = calc_cost(pt_delta, ct_delta)
            session_running_cost += cost_this

            out_kb = output_file.stat().st_size / 1024
            log(f"  STATUS : DONE in {elapsed:.0f}s -> {output_file.name} ({out_kb:.0f} KB)")
            log(f"  TOKENS : prompt={pt_delta:,} | completion={ct_delta:,} | total={tt_delta:,} | calls={calls_delta}")
            log(f"  COST   : ${cost_this:.4f} USD (session running total: ${session_running_cost:.4f})")
            success += 1

            # Persist to master log IMMEDIATELY after every success
            save_token_log(GLOBAL_USAGE, stem, before_usage, status="SUCCESS")
            log(f"  LOG    : token_usage_master.json updated")

        except Exception as e:
            elapsed   = time.time() - t_start
            error_msg = str(e)
            tb_text   = traceback.format_exc()

            log(f"  STATUS : FAILED after {elapsed:.0f}s")
            log(f"  ERROR  : {error_msg}")
            log(f"  TRACEBACK:\n{tb_text}")

            failed += 1
            failed_pdfs.append(pdf_path.name)

            # CRITICAL: log tokens for FAILED PDF too — zero cost data lost
            save_token_log(GLOBAL_USAGE, stem, before_usage,
                           status=f"FAILED: {error_msg[:250]}")

            # Show tokens consumed by the failed PDF
            pt_delta  = GLOBAL_USAGE["prompt_tokens"]    - before_usage["prompt_tokens"]
            ct_delta  = GLOBAL_USAGE["completion_tokens"]- before_usage["completion_tokens"]
            cost_fail = calc_cost(pt_delta, ct_delta)
            session_running_cost += cost_fail
            log(f"  TOKENS : prompt={pt_delta:,} | completion={ct_delta:,} (FAILED PDF — still logged)")
            log(f"  COST   : ${cost_fail:.4f} USD wasted | session total: ${session_running_cost:.4f}")
            log(f"  LOG    : Partial tokens saved to token_usage_master.json")

    # ── STEP 5: Final summary ─────────────────────────────────────────────────
    log("")
    log("=" * 62)
    log("  OncoRAG Indexing Complete")
    log("=" * 62)
    log(f"  Succeeded : {success}")
    log(f"  Failed    : {failed}")
    log(f"  Skipped   : {skipped}")
    log(f"  Total     : {total}")

    # Read back final session data from master log
    session_data = {}
    if TOKEN_LOG_PATH.exists():
        try:
            with open(TOKEN_LOG_PATH, "r", encoding="utf-8") as f:
                log_data = json.load(f)

            for s in log_data.get("all_sessions", []):
                if s.get("session_start") == SESSION_START:
                    session_data = s
                    t = s.get("session_totals", {})
                    log("")
                    log("  THIS SESSION — OncoRAG Cost Summary")
                    log("  " + "-" * 48)
                    log(f"  Prompt tokens     : {t.get('prompt_tokens', 0):>12,}")
                    log(f"  Completion tokens : {t.get('completion_tokens', 0):>12,}")
                    log(f"  Total tokens      : {t.get('total_tokens', 0):>12,}")
                    log(f"  API calls         : {t.get('api_calls', 0):>12,}")
                    log(f"  Estimated cost    :     ${t.get('estimated_cost_usd', 0.0):.4f} USD")
                    log("")
                    log("  Per-PDF breakdown:")
                    for pdf_stem, pd in s.get("pdfs", {}).items():
                        tok   = pd.get("total_tokens", 0)
                        calls = pd.get("api_calls", 0)
                        c     = pd.get("estimated_cost_usd", 0.0)
                        st    = pd.get("status", "?")
                        short = pdf_stem[:46]
                        log(f"    {short:<48s} {tok:>8,} tok | {calls:>3} calls | ${c:.4f} | {st}")
                    break

            grand = log_data.get("grand_total", {})
            if grand:
                log("")
                log("  ALL-TIME GRAND TOTAL (all depts + all sessions)")
                log("  " + "-" * 48)
                log(f"  Total tokens   : {grand.get('total_tokens', 0):>12,}")
                log(f"  Estimated cost : ${grand.get('estimated_cost_usd', 0.0):.4f} USD")

        except Exception as e:
            log(f"  WARN: Could not read back master log: {e}")

    # Write markdown cost report
    if session_data:
        write_cost_report(session_data, failed_pdfs)
    else:
        log("  INFO: No new PDFs processed - no cost report generated")

    if failed_pdfs:
        log("")
        log("  FAILED PDFs (tokens ARE tracked in logs):")
        for fp in failed_pdfs:
            log(f"    - {fp}")

    # Cleanup live tracker
    lp = Path("live_progress.txt")
    if lp.exists():
        try:
            lp.unlink()
        except Exception:
            pass

    log("")
    log(f"  Logs: {LOGS_DIR}")
    log(f"  Index: {RESULTS_DIR}")
    log("=" * 62)


if __name__ == "__main__":
    main()
