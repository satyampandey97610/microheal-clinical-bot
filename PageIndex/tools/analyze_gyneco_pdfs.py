"""
GynecoRAG PDF Pre-Analysis Script
===================================
Checks all Gyneco PDFs before indexing:
- Readability (PyPDF2 + PyMuPDF)
- Page count, size, metadata
- TOC detection hints
- Text extraction quality
"""

import PyPDF2
import pymupdf
from pathlib import Path
import json

PDF_DIR = Path(__file__).parent.parent.parent / "GynecoRAG" / "data"
pdfs = sorted(PDF_DIR.glob("*.pdf"))

print(f"=== GynecoRAG PDF Analysis ({len(pdfs)} files) ===\n")

results = []
for pdf_path in pdfs:
    name = pdf_path.name
    size_mb = pdf_path.stat().st_size / (1024 * 1024)

    # Try PyPDF2
    try:
        reader = PyPDF2.PdfReader(str(pdf_path))
        num_pages_pypdf2 = len(reader.pages)
        meta = reader.metadata
        title_str = meta.title if meta and meta.title else "N/A"
        if len(title_str) > 50:
            title_str = title_str[:50]

        # Check first few pages text extraction
        first_page_text = reader.pages[0].extract_text() or ""
        first_page_chars = len(first_page_text)

        # Check if any page has TOC indicators
        toc_hints = []
        for i in range(min(15, num_pages_pypdf2)):
            pt = (reader.pages[i].extract_text() or "").lower()
            if "table of contents" in pt or "contents" in pt[:30]:
                toc_hints.append(i + 1)
            # Check for TOC-like patterns (dots/numbers)
            if pt.count("...") > 3 or pt.count(". . .") > 3:
                toc_hints.append(i + 1)

        pypdf2_ok = True
    except Exception as e:
        pypdf2_ok = False
        num_pages_pypdf2 = 0
        title_str = "ERROR"
        first_page_chars = 0
        toc_hints = []
        print(f"  PyPDF2 ERROR: {e}")

    # Try PyMuPDF
    try:
        doc = pymupdf.open(str(pdf_path))
        num_pages_mupdf = len(doc)
        first_mupdf_text = doc[0].get_text() if num_pages_mupdf > 0 else ""
        mupdf_chars = len(first_mupdf_text)
        mupdf_ok = True
        doc.close()
    except Exception as e:
        mupdf_ok = False
        num_pages_mupdf = 0
        mupdf_chars = 0
        print(f"  PyMuPDF ERROR: {e}")

    status = "OK" if pypdf2_ok and mupdf_ok else "ISSUE"

    info = {
        "name": name,
        "size_mb": round(size_mb, 1),
        "pages": num_pages_pypdf2,
        "title": title_str,
        "first_page_chars": first_page_chars,
        "mupdf_chars": mupdf_chars,
        "toc_pages": toc_hints,
        "status": status,
    }
    results.append(info)

    title_display = title_str if title_str else "N/A"
    print(f"[{status}] {name}")
    print(f"      Size: {size_mb:.1f} MB | Pages: {num_pages_pypdf2} | Title: {title_display}")
    print(f"      PyPDF2 first page chars: {first_page_chars} | PyMuPDF first page chars: {mupdf_chars}")
    toc_display = toc_hints if toc_hints else "None detected"
    print(f"      TOC hints on pages: {toc_display}")

    # Check for potential problems
    if first_page_chars < 50:
        print(f"      WARNING: Very little text on first page - might be scanned/image PDF")
    if num_pages_pypdf2 > 500:
        print(f"      WARNING: Large PDF ({num_pages_pypdf2} pages) - may need chunking")
    if num_pages_pypdf2 == 0:
        print(f"      CRITICAL: Cannot read PDF")
    print()

print("\n=== Summary ===")
total_pages = sum(r["pages"] for r in results)
print(f"Total PDFs: {len(results)}")
print(f"Total Pages: {total_pages}")
ok_count = sum(1 for r in results if r["status"] == "OK")
print(f"Readable: {ok_count}/{len(results)}")
low_text = [r["name"] for r in results if r["first_page_chars"] < 50]
if low_text:
    print(f"Low text extraction: {low_text}")
