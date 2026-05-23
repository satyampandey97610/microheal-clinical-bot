from pathlib import Path
import json, sys, os

sys.path.insert(0, '.')

print('='*55)
print('  GastroRAG END-TO-END VERIFICATION REPORT')
print('='*55)

# CHECK 1: PDFs
pdfs = sorted(Path('./pdfs').glob('*.pdf'))
print(f'\n[1] PDFs in /pdfs folder: {len(pdfs)}/14')
for p in pdfs:
    print(f'    - {p.name}')

# CHECK 2: JSONs
jsons = sorted(Path('./results').glob('*.json'))
print(f'\n[2] JSON indexes in /results: {len(jsons)}/14')
for j in jsons:
    sz = j.stat().st_size
    ok = 'OK' if sz > 2000 else 'TOO SMALL'
    print(f'    [{ok}] {j.name[:55]} ({sz:,} bytes)')

# CHECK 3: All 14 sources in app.py
from app import DOCUMENTS
print(f'\n[3] Sources in app.py: {len(DOCUMENTS)}/14')
missing = []
for k, v in DOCUMENTS.items():
    exists = v['tree_path'].exists()
    sz = v['tree_path'].stat().st_size if exists else 0
    ok = 'OK' if exists and sz > 2000 else 'MISSING'
    print(f'    [{ok}] {k}: {v["short"]}')
    if ok != 'OK':
        missing.append(k)

# CHECK 4: .env API key
from dotenv import load_dotenv
load_dotenv('.env')
key = os.getenv('OPENAI_API_KEY', '')
key_status = f'FOUND ({key[:12]}...)' if key else 'MISSING'
print(f'\n[4] API Key in .env: {key_status}')

# CHECK 5: Retrieval test
print(f'\n[5] Retrieval pipeline smoke test...')
try:
    from app import retrieve_context_pro
    # Quick retrieval test - won't call LLM, just keyword scoring
    from app import DOCUMENTS, load_document_structure, get_candidates, normalize_text
    total_candidates = 0
    for doc_key, doc_info in DOCUMENTS.items():
        tp = doc_info['tree_path']
        if tp.exists():
            data = load_document_structure(str(tp))
            candidates = get_candidates("GLP-1 treatment", data.get("structure", []), doc_info['short'], doc_info['type'])
            total_candidates += len(candidates)
    print(f'    Candidates found for "GLP-1 treatment": {total_candidates} across all 14 sources')
    retrieval_ok = total_candidates > 0
except Exception as e:
    print(f'    ERROR: {e}')
    retrieval_ok = False

# CHECK 6: Git status
import subprocess
result = subprocess.run(['git', 'log', '--oneline', '-3'], capture_output=True, text=True)
print(f'\n[6] Git log (last 3 commits):')
for line in result.stdout.strip().split('\n'):
    print(f'    {line}')

# FINAL VERDICT
all_ok = (
    len(pdfs) == 14 and
    len(jsons) == 14 and
    len(DOCUMENTS) == 14 and
    len(missing) == 0 and
    bool(key) and
    retrieval_ok
)

print('\n' + '='*55)
if all_ok:
    print('  FINAL VERDICT: ALL SYSTEMS GO - PRODUCTION READY')
else:
    issues = []
    if len(pdfs) != 14: issues.append(f'PDFs: {len(pdfs)}/14')
    if len(jsons) != 14: issues.append(f'JSONs: {len(jsons)}/14')
    if missing: issues.append(f'Missing sources: {missing}')
    if not key: issues.append('API key missing')
    if not retrieval_ok: issues.append('Retrieval failed')
    print(f'  ISSUES: {", ".join(issues)}')
print('='*55)
