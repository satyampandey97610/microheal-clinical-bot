# GeriatricRAG Indexing Cost Report

**Session start** : `2026-06-15T23:53:13.000212`
**Completed**     : `2026-06-16T00:05:32.275267`
**Model**         : gpt-4o-mini (hardcoded)
**Pricing**       : Input $0.15/1M | Output $0.6/1M

---
## Per-PDF Cost Breakdown

| PDF | Pages | Prompt Tok | Compl Tok | Total Tok | API Calls | Cost USD | Status |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| 978-1-62808-976-9_ch15 | 31 | 0 | 0 | 0 | 0 | $0.0000 | FAILED: PyCryptodome is required for AES algorithm |
| Howard_M._Fillit_MD_Kenneth_Rockwood_Kenneth_... | 1160 | 0 | 0 | 0 | 0 | $0.0000 | FAILED: 'list' object has no attribute 'get' |

---
## Session Totals

| Metric | Value |
| :--- | ---: |
| Prompt Tokens     | 0 |
| Completion Tokens | 0 |
| Total Tokens      | 0 |
| API Calls         | 0 |
| **Estimated Cost**| **$0.0000 USD** |

## Failed PDFs (tokens still tracked)

- `978-1-62808-976-9_ch15.pdf`
- `Howard_M._Fillit_MD_Kenneth_Rockwood_Kenneth_Wo.pdf`

---
## Log Files
- Master (JSON) : `logs/token_usage_master.json`
- Raw per-call  : `logs/token_usage_raw.jsonl`
- This report   : `logs/geriatric_cost_report.md`