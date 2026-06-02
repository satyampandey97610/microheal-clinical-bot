"""
Deep Validation — Gyneco PDFs (NO API CALLS, ZERO COST)
=========================================================
Tests EVERY page of EVERY PDF with both PyPDF2 and PyMuPDF.
No tokens used — purely local file validation.
"""

import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))

import PyPDF2
import pymupdf

PDF_DIR = root_dir / "GynecoRAG" / "data"
pdfs = sorted(PDF_DIR.glob("*.pdf"))

print(f"=== DEEP VALIDATION (ZERO COST): {len(pdfs)} Gyneco PDFs ===\n")

all_ok = True
total_pages_validated = 0
pdf_results = []

for pdf_path in pdfs:
    name = pdf_path.name
    print(f"[CHECKING] {name}...")
    issues = []
    
    # Test 1: PyPDF2 full read
    try:
        reader = PyPDF2.PdfReader(str(pdf_path))
        num_pages = len(reader.pages)
        empty_pages = 0
        total_chars = 0
        for i in range(num_pages):
            try:
                text = reader.pages[i].extract_text() or ""
                total_chars += len(text)
                if len(text.strip()) == 0:
                    empty_pages += 1
            except Exception as e:
                issues.append(f"  PyPDF2 page {i+1} FAILED: {e}")
        if empty_pages > 0:
            pct = (empty_pages / num_pages) * 100
            if pct > 80:
                issues.append(f"  WARNING: {empty_pages}/{num_pages} pages empty ({pct:.0f}%) - scanned PDF risk")
    except Exception as e:
        issues.append(f"  PyPDF2 CRITICAL: {e}")
        num_pages = 0
        empty_pages = 0
        total_chars = 0
    
    # Test 2: PyMuPDF full read
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
    except Exception as e:
        issues.append(f"  PyMuPDF CRITICAL: {e}")
        mupdf_pages = 0
        mupdf_empty = 0
        mupdf_chars = 0
    
    size_mb = pdf_path.stat().st_size / (1024 * 1024)
    status = "PASS" if not issues else "FAIL"
    if status == "FAIL":
        all_ok = False
    
    total_pages_validated += num_pages
    est_tokens = total_chars // 4  # rough estimate: ~4 chars per token
    
    result = {
        "name": name,
        "pages": num_pages,
        "empty_pypdf2": empty_pages,
        "empty_mupdf": mupdf_empty,
        "chars": total_chars,
        "est_tokens": est_tokens,
        "size_mb": round(size_mb, 1),
        "status": status,
        "issues": issues,
    }
    pdf_results.append(result)
    
    if issues:
        print(f"  [{status}] {num_pages} pages | ~{est_tokens:,} tokens | {size_mb:.1f} MB")
        for issue in issues:
            print(f"  {issue}")
    else:
        print(f"  [PASS] {num_pages} pages | ~{est_tokens:,} est tokens | {size_mb:.1f} MB | empty: {empty_pages} PyPDF2, {mupdf_empty} MuPDF")
    print()

print("=" * 65)
total_est = sum(r["est_tokens"] for r in pdf_results)
print(f"TOTAL PAGES VALIDATED: {total_pages_validated}")
print(f"TOTAL EST TOKENS (raw text): ~{total_est:,}")
passed = sum(1 for r in pdf_results if r["status"] == "PASS")
failed = sum(1 for r in pdf_results if r["status"] == "FAIL")
print(f"PASSED: {passed}/{len(pdf_results)} | FAILED: {failed}/{len(pdf_results)}")

if all_ok:
    print("\nALL PDFs VALIDATED SUCCESSFULLY - Safe to proceed with indexing!")
else:
    print("\nSOME PDFs HAVE ISSUES:")
    for r in pdf_results:
        if r["status"] == "FAIL":
            print(f"  PROBLEM: {r['name']}")
            for issue in r["issues"]:
                print(f"    {issue}")

print("\n=== Recommended Indexing Order (small -> large) ===")
sorted_results = sorted(pdf_results, key=lambda x: x["pages"])
for i, r in enumerate(sorted_results, 1):
    tag = " [WATCH]" if r["empty_pypdf2"] > r["pages"] * 0.5 else ""
    print(f"  {i:2d}. [{r['pages']:>4d}p] {r['name'][:58]}{tag}")
