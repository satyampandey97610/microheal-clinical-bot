import os
from PyPDF2 import PdfReader

pdfs_dir = r"c:\Satyam_Onedrive\OneDrive\Desktop\New folder\gastroRAG\PageIndex\pdfs"
results_dir = r"c:\Satyam_Onedrive\OneDrive\Desktop\New folder\gastroRAG\PageIndex\results"

left_files = []
for f in os.listdir(pdfs_dir):
    if f.endswith(".pdf"):
        stem = os.path.splitext(f)[0]
        if not os.path.exists(os.path.join(results_dir, f"{stem}_structure.json")):
            left_files.append(f)

total_pages = 0
print(f"{'PDF Name':<60} | {'Pages':<5}")
print("-" * 68)
for f in left_files:
    try:
        reader = PdfReader(os.path.join(pdfs_dir, f))
        pages = len(reader.pages)
        print(f"{f:<60} | {pages:<5}")
        total_pages += pages
    except Exception as e:
        print(f"{f:<60} | Error")

print("-" * 68)
print(f"{'TOTAL PAGES LEFT':<60} | {total_pages:<5}")
