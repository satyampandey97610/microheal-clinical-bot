"""
OncoRAG PDF Deep Pre-Analysis Script
======================================
ZERO COST — No API calls, no tokens used.
Checks all 10 Oncology PDFs before indexing:
- Readability with both PyPDF2 and PyMuPDF
- Page count, size, estimated token count
- TOC detection hints (pages 1-25)
- Empty/scanned page detection
- Author/copyright heavy front-matter detection
- Recommended smart indexing order (small -> large)

Run from: Medical RAG/
    python PageIndex/tools/analyze_onco_pdfs.py
"""

import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))

import PyPDF2
import pymupdf

PDF_DIR = root_dir / "OncoRAG" / "data"
pdfs = sorted(PDF_DIR.glob("*.pdf"))

print(f"=== DEEP VALIDATION (ZERO COST): {len(pdfs)} OncoRAG PDFs ===\n")

all_ok = True
total_pages_validated = 0
pdf_results = []

for pdf_path in pdfs:
    name = pdf_path.name
    print(f"[CHECKING] {name}...")
    issues = []

    # ── Test 1: PyPDF2 full read ──────────────────────────────────────
    try:
        reader = PyPDF2.PdfReader(str(pdf_path))
        num_pages = len(reader.pages)
        empty_pages = 0
        total_chars = 0
        author_heavy_pages = 0   # front pages with <200 chars (title/author/copyright)

        for i in range(num_pages):
            try:
                text = reader.pages[i].extract_text() or ""
                total_chars += len(text)
                if len(text.strip()) == 0:
                    empty_pages += 1
                # Short text in first 20 pages = author/title/copyright clutter
                if i < 20 and len(text.strip()) < 200:
                    author_heavy_pages += 1
            except Exception as e:
                issues.append(f"  PyPDF2 page {i+1} FAILED: {e}")

        # TOC detection on first 25 pages
        toc_hints = []
        for i in range(min(25, num_pages)):
            pt = (reader.pages[i].extract_text() or "").lower()
            if "table of contents" in pt or "contents" in pt[:100]:
                toc_hints.append(i + 1)
            if pt.count("...") > 3 or pt.count(". . .") > 3:
                toc_hints.append(i + 1)
        toc_hints = sorted(set(toc_hints))

        if empty_pages > 0:
            pct = (empty_pages / num_pages) * 100
            if pct > 80:
                issues.append(
                    f"  WARNING: {empty_pages}/{num_pages} pages empty "
                    f"({pct:.0f}%) - likely scanned/image PDF"
                )
        pypdf2_ok = True
    except Exception as e:
        issues.append(f"  PyPDF2 CRITICAL: {e}")
        num_pages = 0
        empty_pages = 0
        total_chars = 0
        author_heavy_pages = 0
        toc_hints = []
        pypdf2_ok = False

    # ── Test 2: PyMuPDF full read ─────────────────────────────────────
    try:
        doc = pymupdf.open(str(pdf_path))
        mupdf_pages = len(doc)
        mupdf_empty = 0
        mupdf_chars = 0
        for i in range(mupdf_pages):
            try:
                text = doc[i].get_text()
                mupdf_chars += len(text)
                if len(text.strip()) == 0:
                    mupdf_empty += 1
            except Exception as e:
                issues.append(f"  PyMuPDF page {i+1} FAILED: {e}")
        doc.close()
        mupdf_ok = True
    except Exception as e:
        issues.append(f"  PyMuPDF CRITICAL: {e}")
        mupdf_pages = 0
        mupdf_empty = 0
        mupdf_chars = 0
        mupdf_ok = False

    size_mb = pdf_path.stat().st_size / (1024 * 1024)
    status = "PASS" if not issues else "WARN"
    if status == "WARN":
        all_ok = False

    total_pages_validated += num_pages
    est_tokens = total_chars // 4   # ~4 chars per token rough estimate

    result = {
        "name": name,
        "pages": num_pages,
        "empty_pypdf2": empty_pages,
        "mupdf_empty": mupdf_empty,
        "chars": total_chars,
        "est_tokens": est_tokens,
        "size_mb": round(size_mb, 1),
        "status": status,
        "issues": issues,
        "toc_hints": toc_hints,
        "author_heavy_pages": author_heavy_pages,
    }
    pdf_results.append(result)

    toc_display = str(toc_hints) if toc_hints else "None detected"
    print(f"  [{status}] {num_pages} pages | ~{est_tokens:,} est tokens | {size_mb:.1f} MB")
    print(f"  Empty pages: {empty_pages} (PyPDF2) | {mupdf_empty} (MuPDF)")
    print(f"  Author/short front-matter pages (first 20): {author_heavy_pages}")
    print(f"  TOC hints on pages: {toc_display}")
    for issue in issues:
        print(f"  {issue}")
    print()

# ── Summary ───────────────────────────────────────────────────────────────
print("=" * 70)
total_est = sum(r["est_tokens"] for r in pdf_results)
print(f"TOTAL PAGES VALIDATED   : {total_pages_validated}")
print(f"TOTAL EST TOKENS (text) : ~{total_est:,}")
passed = sum(1 for r in pdf_results if r["status"] == "PASS")
warned = sum(1 for r in pdf_results if r["status"] == "WARN")
print(f"PASSED: {passed}/{len(pdf_results)} | WARNED: {warned}/{len(pdf_results)}")

print()
print("=== Recommended Indexing Order (small -> large by pages) ===")
sorted_results = sorted(pdf_results, key=lambda x: x["pages"])
for i, r in enumerate(sorted_results, 1):
    tag_scan = " [SCANNED?]" if r["empty_pypdf2"] > r["pages"] * 0.5 else ""
    tag_front = " [HEAVY_FRONT_MATTER]" if r["author_heavy_pages"] > 5 else ""
    print(
        f"  {i:2d}. [{r['pages']:>4d}p | ~{r['est_tokens']:>7,}tok | {r['size_mb']:>5.1f}MB]"
        f"  {r['name'][:52]}{tag_scan}{tag_front}"
    )

if all_ok:
    print("\n[OK] ALL PDFs VALIDATED - Safe to proceed with indexing!")
else:
    print("\n⚠️  SOME PDFs HAVE WARNINGS:")
    for r in pdf_results:
        if r["status"] == "WARN":
            print(f"  WARN: {r['name']}")
            for issue in r["issues"]:
                print(f"    {issue}")
