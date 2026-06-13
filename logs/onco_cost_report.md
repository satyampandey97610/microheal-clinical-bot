# OncoRAG Indexing Cost Report

**Session start** : `2026-06-13T12:32:12.045313`
**Completed**     : `2026-06-13T14:40:29.117687`
**Model**         : gpt-4o-mini (hardcoded)
**Pricing**       : Input $0.15/1M | Output $0.6/1M

---
## Per-PDF Cost Breakdown

| PDF | Pages | Prompt Tok | Compl Tok | Total Tok | API Calls | Cost USD | Status |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| 22.-Textbook-of-Medical-Oncology-Fourth-Editi... | 476 | 21,645,476 | 781,406 | 22,426,882 | 8408 | $3.7157 | SUCCESS |

---
## Session Totals

| Metric | Value |
| :--- | ---: |
| Prompt Tokens     | 21,645,476 |
| Completion Tokens | 781,406 |
| Total Tokens      | 22,426,882 |
| API Calls         | 8,408 |
| **Estimated Cost**| **$3.7157 USD** |

---
## Log Files
- Master (JSON) : `logs/token_usage_master.json`
- Raw per-call  : `logs/token_usage_raw.jsonl`
- This report   : `logs/onco_cost_report.md`