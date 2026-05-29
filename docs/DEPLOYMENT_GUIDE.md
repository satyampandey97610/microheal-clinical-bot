# MicroHeal Clinical Bot — Deployment Guide

## System Status: DEPLOYMENT READY

### What's Included
- **Unified Clinical Engine**: `clinical_engine.py` — platform-independent brain
- **Quad-Domain Support**: Gastroenterology (14 sources) + Cardiology (14 sources) + Nephrology (13 sources) + Neurology (12 sources)
- **Streamlit Frontend**: `app.py` — thin UI layer for testing and demo
- **Agent Wrappers**: `gastro_agent.py`, `cardio_agent.py`, `nephro_agent.py`, and `neuro_agent.py` for direct integration

---

## Deployment Options

### Option 1: Streamlit Cloud
1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo, set `app.py` as the main file
4. Add `OPENAI_API_KEY` in Streamlit Secrets

### Option 2: Docker
```bash
docker build -t microheal-clinical-bot .
docker run -p 8501:8501 --env-file .env microheal-clinical-bot
```

### Option 3: WhatsApp Bot / Workflow Integration
```python
from clinical_engine import ClinicalEngine

engine = ClinicalEngine("gastro")  # or "cardio", "nephro", "neuro"
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
| File | Purpose |
|------|---------|
| `clinical_engine.py` | Core brain — import from any system |
| `app.py` | Streamlit UI frontend |
| `GastroRAG/gastro_agent.py` | Gastro specialist wrapper |
| `CardioRAG/cardio_agent.py` | Cardio specialist wrapper |
| `NephroRAG/nephro_agent.py` | Nephrology specialist wrapper |
| `NeuroRAG/neuro_agent.py` | Neurology specialist wrapper |
| `GastroRAG/index/` | 14 Gastro indexed JSON files |
| `CardioRAG/index/` | 14 Cardio indexed JSON files |
| `NephroRAG/index/` | 13 Nephrology indexed JSON files |
| `NeuroRAG/index/` | 12 Neurology indexed JSON files |
| `requirements.txt` | Python dependencies |
| `config.yaml` | Model and token configuration |
