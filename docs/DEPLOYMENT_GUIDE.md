# MicroHeal Clinical Bot — Deployment Guide

## System Status: DEPLOYMENT READY

### What's Included
- **Unified Clinical Engine**: `clinical_engine.py` — platform-independent brain
- **Octa-Domain Support**:
  - Gastroenterology (14 sources)
  - Cardiology (15 sources)
  - Nephrology (13 sources)
  - Neurology (12 sources)
  - Gynecology (12 sources)
  - Oncology (10 sources)
  - Orthopedics (8 sources)
  - Geriatrics (7 sources)
- **Streamlit Frontend**: `app.py` — thin UI layer for testing and demo
- **Agent Wrappers**: Direct wrappers in each department folder (e.g. `gastro_agent.py`, `cardio_agent.py`, etc.) for direct integration

---

## Deployment Options

### Option 1: Streamlit Cloud
1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo, set `app.py` as the main file
4. Add `OPENAI_API_KEY` in Streamlit Secrets

### Option 2: Docker (Production Ready with Nginx)
The container uses Nginx to serve both Streamlit (`/`) and FastAPI (`/query`) on a single port (8501) with full WebSocket support.
```bash
docker build -t microheal-clinical-bot .
docker run -d -p 8501:8501 --env-file .env microheal-clinical-bot
```

### Option 3: WhatsApp Bot / Workflow Integration
```python
from clinical_engine import ClinicalEngine

engine = ClinicalEngine("gastro")  # or "cardio", "nephro", "neuro", "gyneco", "onco", "ortho", "geriatric"
result = engine.query("What is GERD?")
# result["answer"] → Clinical response
# result["sources"] → Real citations (empty if none used)
# result["out_of_domain"] → True if wrong specialty
```

---

## Environment Variables
| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key for GPT models |

---

## File Structure
| File / Directory | Purpose |
|------------------|---------|
| `clinical_engine.py` | Core brain — import from any system |
| `api.py` | FastAPI backend |
| `app.py` | Streamlit UI frontend |
| `nginx.conf` | Reverse proxy routing for API and UI |
| `GastroRAG/gastro_agent.py` | Gastro specialist wrapper |
| `CardioRAG/cardio_agent.py` | Cardio specialist wrapper |
| `NephroRAG/nephro_agent.py` | Nephrology specialist wrapper |
| `NeuroRAG/neuro_agent.py` | Neurology specialist wrapper |
| `GynecoRAG/gyneco_agent.py` | Gynecology specialist wrapper |
| `OncoRAG/onco_agent.py` | Oncology specialist wrapper |
| `OrthopedicsRAG/orthopedic_agent.py` | Orthopedics specialist wrapper |
| `GeriatricRAG/geriatric_agent.py` | Geriatrics specialist wrapper |
| `GastroRAG/index/` | 14 Gastro indexed JSON files |
| `CardioRAG/index/` | 15 Cardio indexed JSON files |
| `NephroRAG/index/` | 13 Nephrology indexed JSON files |
| `NeuroRAG/index/` | 12 Neurology indexed JSON files |
| `GynecoRAG/index/` | 12 Gynecology indexed JSON files |
| `OncoRAG/index/` | 10 Oncology indexed JSON files |
| `OrthopedicsRAG/index/` | 8 Orthopedics indexed JSON files |
| `GeriatricRAG/index/` | 7 Geriatrics indexed JSON files |
| `requirements.txt` | Python dependencies |
| `config.yaml` | Model and token configuration |

