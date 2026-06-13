"""
OncoRAG Pre-Flight Verification Script
========================================
Checks EVERYTHING before indexing starts:
  1. Python dependencies
  2. PageIndex engine imports
  3. API key
  4. Directory structure
  5. All 10 PDFs - full integrity (PyPDF2 + PyMuPDF)
  6. Log file infrastructure
  7. Already-indexed status

Run from Medical RAG/:
    python PageIndex/tools/preflight_onco.py
"""

import sys
import os
import json
import importlib
from pathlib import Path

root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

print("=" * 65)
print("  ONCORAG PRE-FLIGHT VERIFICATION (ZERO COST)")
print("=" * 65)

all_ok = True
errors = []
warnings = []

# ─────────────────────────────────────────────────────
# 1. Python dependencies
# ─────────────────────────────────────────────────────
print("\n[1/7] Checking Python dependencies...")
REQUIRED_DEPS = [
    ("litellm",    "litellm"),
    ("PyPDF2",     "PyPDF2"),
    ("pymupdf",    "pymupdf"),
    ("dotenv",     "python-dotenv"),
    ("yaml",       "pyyaml"),
    ("tiktoken",   "tiktoken"),
    ("json",       "built-in"),
    ("traceback",  "built-in"),
]
for module_name, package_name in REQUIRED_DEPS:
    try:
        importlib.import_module(module_name)
        print(f"   OK   {module_name}")
    except ImportError as e:
        print(f"   FAIL {module_name} (install: pip install {package_name}): {e}")
        errors.append(f"Missing dependency: {module_name}")
        all_ok = False

# ─────────────────────────────────────────────────────
# 2. PageIndex engine import
# ─────────────────────────────────────────────────────
print("\n[2/7] Checking PageIndex engine imports...")
try:
    from PageIndex.pageindex.page_index import page_index_main
    print("   OK   page_index_main")
except Exception as e:
    print(f"   FAIL page_index_main: {e}")
    errors.append(f"page_index_main import failed: {e}")
    all_ok = False

try:
    from PageIndex.pageindex.utils import ConfigLoader, GLOBAL_USAGE
    print("   OK   ConfigLoader, GLOBAL_USAGE")
except Exception as e:
    print(f"   FAIL ConfigLoader/GLOBAL_USAGE: {e}")
    errors.append(f"ConfigLoader import failed: {e}")
    all_ok = False

# ─────────────────────────────────────────────────────
# 3. API key
# ─────────────────────────────────────────────────────
print("\n[3/7] Checking OpenAI API key...")
from dotenv import load_dotenv
load_dotenv(dotenv_path=root_dir / ".env")
api_key = os.getenv("OPENAI_API_KEY", "")
if api_key and api_key.startswith("sk-"):
    print(f"   OK   OPENAI_API_KEY found: {api_key[:14]}...")
else:
    print("   FAIL OPENAI_API_KEY missing or does not start with 'sk-'")
    errors.append("API key missing or invalid")
    all_ok = False

# ─────────────────────────────────────────────────────
# 4. Directory structure
# ─────────────────────────────────────────────────────
print("\n[4/7] Checking directories...")

pdf_dir   = root_dir / "OncoRAG" / "data"
index_dir = root_dir / "OncoRAG" / "index"
logs_dir  = root_dir / "logs"

for d, label in [(pdf_dir, "OncoRAG/data"), (logs_dir, "logs")]:
    if d.exists():
        print(f"   OK   {label}: {d}")
    else:
        print(f"   FAIL {label} MISSING: {d}")
        errors.append(f"Directory missing: {d}")
        all_ok = False

# Create index dir if needed
try:
    index_dir.mkdir(parents=True, exist_ok=True)
    print(f"   OK   OncoRAG/index (ready): {index_dir}")
except Exception as e:
    print(f"   FAIL Cannot create index dir: {e}")
    errors.append(f"Cannot create index dir: {e}")
    all_ok = False

# ─────────────────────────────────────────────────────
# 5. PDF integrity check (PyPDF2 + PyMuPDF)
# ─────────────────────────────────────────────────────
print("\n[5/7] Checking all 10 OncoRAG PDFs (PyPDF2 + PyMuPDF)...")

import PyPDF2
import pymupdf

INDEXING_ORDER = [
    ("Dtsch_Arztebl_Int-120_445.pdf",           2,    "journal"),
    ("aids-37-1871.pdf",                          12,   "journal"),
    ("dmm-16-050175.pdf",                         15,   "research"),
    ("tbad017.pdf",                               17,   "journal"),
    ("WHO-MHP-HPS-EML-2023.02-eng.pdf",          71,   "who_ref"),
    ("Padova_lectures_vers3.pdf",                 123,  "lectures"),
    ("ProstateBook2.pdf",                         184,  "textbook"),
    ("22.-Textbook-of-Medical-Oncology-Fourth-Edition-Cavalli-Textbook-of-Medical-Oncology-PDFDrive-.pdf", 476, "textbook"),
    ("Oxford-Handbook-of-Oncology-4th-Ed.pdf",   897,  "handbook"),
    ("The MD Anderson Manual of Medical Oncology 3e.pdf", 1274, "manual"),
]

pdf_results = []
for fname, expected_pages, doc_type in INDEXING_ORDER:
    p = pdf_dir / fname
    if not p.exists():
        print(f"   FAIL MISSING: {fname}")
        errors.append(f"PDF file missing: {fname}")
        all_ok = False
        pdf_results.append({"name": fname, "ok": False, "reason": "FILE MISSING"})
        continue

    size_mb = p.stat().st_size / (1024 * 1024)
    pdf_issues = []

    # PyPDF2 check
    pypdf2_pages = 0
    try:
        reader = PyPDF2.PdfReader(str(p))
        pypdf2_pages = len(reader.pages)
        # Check first + last page readable
        first_text = reader.pages[0].extract_text() or ""
        last_text  = reader.pages[-1].extract_text() or ""
        if pypdf2_pages == 0:
            pdf_issues.append("0 pages (PyPDF2)")
    except Exception as e:
        pdf_issues.append(f"PyPDF2 error: {e}")

    # PyMuPDF check
    mupdf_pages = 0
    try:
        doc = pymupdf.open(str(p))
        mupdf_pages = len(doc)
        doc.close()
        if mupdf_pages == 0:
            pdf_issues.append("0 pages (MuPDF)")
    except Exception as e:
        pdf_issues.append(f"MuPDF error: {e}")

    # Page count agreement check
    if pypdf2_pages > 0 and mupdf_pages > 0 and abs(pypdf2_pages - mupdf_pages) > 5:
        pdf_issues.append(f"Page count mismatch: PyPDF2={pypdf2_pages} vs MuPDF={mupdf_pages}")

    if pdf_issues:
        status = "WARN"
        warnings.extend(pdf_issues)
        for issue in pdf_issues:
            print(f"   WARN {fname[:52]}: {issue}")
    else:
        status = "OK"
        short = fname[:52]
        print(f"   OK   {short}")
        print(f"        {pypdf2_pages}p PyPDF2 | {mupdf_pages}p MuPDF | {size_mb:.1f} MB | type={doc_type}")

    pdf_results.append({
        "name": fname,
        "ok": status == "OK",
        "pypdf2_pages": pypdf2_pages,
        "mupdf_pages": mupdf_pages,
        "size_mb": round(size_mb, 1),
    })

# ─────────────────────────────────────────────────────
# 6. Log infrastructure check
# ─────────────────────────────────────────────────────
print("\n[6/7] Checking log infrastructure...")

raw_log    = logs_dir / "token_usage_raw.jsonl"
master_log = logs_dir / "token_usage_master.json"
cost_rpt   = logs_dir / "onco_cost_report.md"

if raw_log.exists():
    raw_size_kb = raw_log.stat().st_size / 1024
    # Count lines
    with open(raw_log, "r", encoding="utf-8") as f:
        line_count = sum(1 for _ in f)
    print(f"   OK   token_usage_raw.jsonl ({raw_size_kb:.0f} KB, {line_count:,} entries)")
else:
    print("   INFO token_usage_raw.jsonl: will be created on first API call")

if master_log.exists():
    master_size_kb = master_log.stat().st_size / 1024
    try:
        with open(master_log, "r", encoding="utf-8") as f:
            log_data = json.load(f)
        num_sessions = len(log_data.get("all_sessions", []))
        grand = log_data.get("grand_total", {})
        grand_tokens = grand.get("total_tokens", 0)
        grand_cost = grand.get("estimated_cost_usd", 0.0)
        print(
            f"   OK   token_usage_master.json ({master_size_kb:.0f} KB) "
            f"| {num_sessions} sessions "
            f"| Grand total: {grand_tokens:,} tokens"
            f" | Est. cost: ${grand_cost:.4f}"
        )
    except Exception as e:
        print(f"   WARN token_usage_master.json exists but could not parse: {e}")
        warnings.append(f"token_usage_master.json parse error: {e}")
else:
    print("   INFO token_usage_master.json: will be created on first PDF")

if cost_rpt.exists():
    print(f"   INFO onco_cost_report.md: exists from previous run (will overwrite)")
else:
    print("   INFO onco_cost_report.md: will be created after indexing")

# ─────────────────────────────────────────────────────
# 7. Already-indexed status
# ─────────────────────────────────────────────────────
print("\n[7/7] Indexing status for each PDF...")

already_done = []
to_index     = []

for fname, expected_pages, doc_type in INDEXING_ORDER:
    stem     = Path(fname).stem
    out_file = index_dir / f"{stem}_structure.json"
    if out_file.exists():
        size_kb = out_file.stat().st_size / 1024
        print(f"   SKIP {fname[:52]}")
        print(f"        Output: {out_file.name} ({size_kb:.0f} KB)")
        already_done.append(fname)
    else:
        print(f"   TODO {fname[:52]}")
        to_index.append(fname)

# ─────────────────────────────────────────────────────
# FINAL SUMMARY
# ─────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("  PRE-FLIGHT SUMMARY")
print("=" * 65)
pdf_ok_count = sum(1 for r in pdf_results if r.get("ok"))
print(f"  PDFs readable        : {pdf_ok_count}/{len(INDEXING_ORDER)}")
print(f"  Already indexed      : {len(already_done)}/{len(INDEXING_ORDER)}")
print(f"  Needs indexing       : {len(to_index)}")
print(f"  Hard errors          : {len(errors)}")
print(f"  Warnings             : {len(warnings)}")

if to_index:
    print(f"\n  PDFs to index (in order):")
    for i, f in enumerate(to_index, 1):
        print(f"    {i:2d}. {f}")

if errors:
    print("\n  ERRORS (must fix before running):")
    for e in errors:
        print(f"    - {e}")
    print("\n  STATUS: ABORT -- Fix all errors before indexing!")
    sys.exit(1)
elif warnings:
    print("\n  WARNINGS (non-blocking):")
    for w in warnings:
        print(f"    - {w}")
    print("\n  STATUS: PROCEED WITH CAUTION")
else:
    print("\n  STATUS: ALL CLEAR -- Safe to start indexing!")
    if to_index:
        print(f"  Run: python PageIndex/tools/batch_index_onco.py")
    else:
        print("  All PDFs already indexed!")
