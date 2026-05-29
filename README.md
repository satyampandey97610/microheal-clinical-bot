<div align="center">
  <img src="https://cdn-icons-png.flaticon.com/512/3004/3004458.png" width="80" alt="MicroHeal Logo">
  <h1>MicroHeal Clinical Bot</h1>
  <p><b>Unified Gastroenterology, Cardiology, Nephrology & Neurology RAG Assistant</b></p>
  <p><i>A quad-specialty, clinically-accurate AI powered by Retrieval-Augmented Generation (RAG).</i></p>
</div>

---

## 🎯 System Overview

**MicroHeal Clinical Bot** is a production-ready AI application that acts as a specialized clinical assistant. It fuses a local indexed knowledge base of **53 medical textbooks, journals, and guidelines** with state-of-the-art LLM reasoning.

Users can switch between four isolated specialist engines:
- 🩺 **Gastroenterology Expert** — 14 GI sources including casebooks, GLP-1 research, and clinical datasets.
- ❤️ **Cardiology Expert** — 14 cardiovascular sources including ACC/AHA guidelines, ESC protocols, and heart failure studies.
- 💧 **Nephrology Expert** — 13 kidney health sources including KDIGO guidelines, clinical handbooks, and textbook references.
- 🧠 **Neurology Expert** — 12 neuroscience sources including Harrison’s Neurology chapters, WHO neurological disorders, AHA stroke guidelines, and clinical case studies.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| **LLM-Powered Domain Isolation** | Uses GPT intelligence to classify queries — no hardcoded keyword lists. Each specialist only answers its own domain. |
| **Real Evidence Only** | Citations are shown ONLY when the answer is derived from the indexed knowledge base. No fake references ever. |
| **Dynamic Registry** | Zero hardcoded paths. Automatically scans and loads all available index files on startup. |
| **Platform-Independent Engine** | The core brain (`clinical_engine.py`) has no UI dependency. Import it from WhatsApp bots, APIs, workflows, or any system. |
| **Conversational Intelligence** | Handles greetings, casual chat, and clinical questions naturally — no rigid format for simple conversations. |
| **Hindi/Hinglish Support** | Detects Hinglish queries and responds in Hindi automatically. |

---

## 🏗️ Architecture

```
MicroHeal Clinical Bot
├── clinical_engine.py      ← The core brain (import from anywhere)
├── app.py                  ← Streamlit UI (thin skin over the engine)
├── GastroRAG/
│   ├── gastro_agent.py     ← Gastro wrapper with query_gastro()
│   ├── index/              ← 14 indexed JSON knowledge files
│   └── data/               ← Source PDFs
├── CardioRAG/
│   ├── cardio_agent.py     ← Cardio wrapper with query_cardio()
│   ├── index/              ← 14 indexed JSON knowledge files
│   └── data/               ← Source PDFs
├── NephroRAG/
│   ├── nephro_agent.py     ← Nephro wrapper with query_nephro()
│   ├── index/              ← 13 indexed JSON knowledge files
│   └── data/               ← Source PDFs
├── NeuroRAG/
│   ├── neuro_agent.py      ← Neuro wrapper with query_neuro()
│   ├── index/              ← 12 indexed JSON knowledge files
│   └── data/               ← Source PDFs
├── PageIndex/              ← PDF indexing pipeline
├── docs/                   ← Deployment guide
├── logs/                   ← Processing logs
├── Dockerfile
├── requirements.txt
└── .env
```

---

## 🚀 Quick Start

### 1. Clone & Install
```bash
git clone https://github.com/satyampandey97610/microheal-clinical-bot.git
cd microheal-clinical-bot
pip install -r requirements.txt
```

### 2. Set API Key
```bash
# Create .env file
echo "OPENAI_API_KEY=sk-your-key-here" > .env
```

### 3. Run the Streamlit App
```bash
streamlit run app.py
```

### 4. Use in Your Own Code (WhatsApp Bot, API, etc.)
```python
from clinical_engine import ClinicalEngine

# Initialize the specialist you need
gastro = ClinicalEngine("gastro")
cardio = ClinicalEngine("cardio")
nephro = ClinicalEngine("nephro")
neuro = ClinicalEngine("neuro")

# Query it
result = gastro.query("What causes GERD?")
print(result["answer"])     # The clinical response
print(result["sources"])    # Real sources (empty if none used)
print(result["out_of_domain"])  # True if wrong specialty

# Neurology example
result = neuro.query("What is intracerebral hemorrhage management?")
print(result["answer"])

# With conversation history
history = [
    {"role": "user", "content": "What is acid reflux?"},
    {"role": "assistant", "content": "Acid reflux is..."}
]
result = gastro.query("How is it treated?", history=history)
```

---

## 📚 Knowledge Base (53 Indexed Sources)

### Gastroenterology (14 Sources)
| # | Source | Type |
|---|--------|------|
| 1 | Yamada's Handbook of Gastroenterology (2019) | Handbook |
| 2 | First Principles of Gastroenterology & Hepatology | Textbook |
| 3 | Casebook in Gastroenterology | Casebook |
| 4 | EMJ Gastroenterology Vol.10.1 (2021) | Journal |
| 5 | GLP-1 Research Article (2023) | Journal |
| 6 | GLP-1 Clinical Study (e002519) | Journal |
| 7 | Frontiers in Clinical Diabetes — GLP-1 | Journal |
| 8 | GLP-1s and Diet | Guide |
| 9 | Nutritional Priorities for GLP-1 Therapy | Guide |
| 10 | The Ultimate GLP-1 Diet Cookbook | Guide |
| 11 | Protein Balance Sample Meal Plan | Guide |
| 12 | Your Ultimate Guide to GLP-1 Medications | Guide |
| 13 | GI Disease Clinical Dataset (30,560 records) | Dataset |
| 14 | DigestiveDataSets CRAN | Dataset |

### Cardiology (14 Sources)
| # | Source | Type |
|---|--------|------|
| 1 | Oxford Cardiology Book | Textbook |
| 2 | ESC Guideline ACS 2023 | Guideline |
| 3 | ESC Guidelines 2022 — Ventricular Arrhythmias | Guideline |
| 4 | ESC CCS 2024 Guideline | Guideline |
| 5 | 2024 ESC Compressed | Guideline |
| 6 | ACC/AHA Primary Prevention (2019) | Guideline |
| 7 | ACC/AHA Heart Failure Management (2022) | Guideline |
| 8 | ACC/AHA Aortic Disease (2022) | Guideline |
| 9 | ACC/AHA Chest Pain Evaluation (2021) | Guideline |
| 10 | ACC/AHA/HRS AF Management (2019) | Guideline |
| 11 | ACC/AHA/ACCP/HRS AF Diagnosis (2023) | Guideline |
| 12 | ESC Guideline — ehab368 | Guideline |
| 13 | ESC Guideline — ehad193 | Guideline |
| 14 | Heart Disease Prevention (Côté) | Reference |

### Nephrology (13 Sources)
| # | Source | Type |
|---|--------|------|
| 1 | Nephrology for Medical Students | Textbook |
| 2 | Clinical Handbook of Nephrology (2024) | Reference |
| 3 | KDIGO 2012 CKD Guideline | Guideline |
| 4 | KDIGO 2017 CKD-MBD Guideline Update | Guideline |
| 5 | KDIGO 2021 Glomerular Diseases Guideline | Guideline |
| 6 | KDIGO 2024 CKD Guideline | Guideline |
| 7 | KDIGO 2024 CKD Guideline — Executive Summary | Guideline |
| 8 | KDIGO 2025 ADPKD Guideline | Guideline |
| 9 | KDIGO 2025 ADPKD Guideline — Executive Summary | Guideline |
| 10 | KDIGO 2025 Nephrotic Syndrome in Children | Guideline |
| 11 | KDIGO Glomerular Diseases Guideline 2021 (LN-2024 Update) | Guideline |
| 12 | Nephrology Clinical Manual (0071449035) | Reference |
| 13 | Nephrology Therapeutic Guide (therap) | Reference |

### Neurology (12 Sources)
| # | Source | Type |
|---|--------|------|
| 1 | Harrison’s Principles of Internal Medicine — Neurology Part 1 | Textbook |
| 2 | Harrison’s Principles of Internal Medicine — Neurology Part 2 | Textbook |
| 3 | Harrison’s Principles of Internal Medicine — Neurology Part 3 (Chunk 1) | Textbook |
| 4 | Harrison’s Principles of Internal Medicine — Neurology Part 3 (Chunk 2) | Textbook |
| 5 | Harrison’s Principles of Internal Medicine — Neurology Part 3 (Chunk 3) | Textbook |
| 6 | Harrison’s Principles of Internal Medicine — Neurology Part 3 (Chunk 4) | Textbook |
| 7 | WHO Neurological Disorders: Public Health Challenges | Reference |
| 8 | 20 Common Neurological Disorders | Reference |
| 9 | A Saga of Indian Neurology | Reference |
| 10 | AHA/ASA Spontaneous Intracerebral Hemorrhage Guideline (2022) | Guideline |
| 11 | European Neurology — ENE-27-1805 | Journal |
| 12 | Teaching NeuroImages: Venous System & DVA | Journal |

---

## 🐳 Docker Deployment

```bash
docker build -t microheal-clinical-bot .
docker run -p 8501:8501 --env-file .env microheal-clinical-bot
```

---

## 📄 License

This project is intended for educational and research purposes only. Always consult a qualified healthcare professional for medical advice.
