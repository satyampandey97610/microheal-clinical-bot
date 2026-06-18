<<<<<<< HEAD
<div align="center">
  <img src="https://cdn-icons-png.flaticon.com/512/3004/3004458.png" width="80" alt="MicroHeal Logo">
  <h1>MicroHeal Clinical Bot</h1>
  <p><b>Unified Gastroenterology, Cardiology, Nephrology, Neurology, Gynecology, Oncology, Orthopedics & Geriatrics RAG Assistant</b></p>
  <p><i>An octa-specialty, clinically-accurate AI powered by Retrieval-Augmented Generation (RAG).</i></p>
</div>
=======
# 🩺 GastroRAG: Elite Gastroenterology Clinical Intelligence

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/frontend-streamlit-FF4B4B.svg)](https://streamlit.io/)
[![Engine: PageIndex](https://img.shields.io/badge/engine-PageIndex-000000.svg)](https://github.com/VectifyAI/PageIndex)
[![Model: GPT--4o](https://img.shields.io/badge/llm-GPT--4o-412991.svg)](https://openai.com/)

**GastroRAG** is a production-grade clinical decision support system (CDSS) designed for professional gastroenterologists. Unlike traditional vector-based RAG, it utilizes the **PageIndex** engine to perform reasoning-based retrieval across a high-density clinical knowledge base, ensuring unprecedented accuracy and traceability.
>>>>>>> 848bcc72937d70826d927480a4dc9666f03d2386

---

## 🛠️ Technology Stack

<<<<<<< HEAD
**MicroHeal Clinical Bot** is a production-ready AI application that acts as a specialized clinical assistant. It fuses a local indexed knowledge base of **80 medical textbooks, journals, and guidelines** with state-of-the-art LLM reasoning.

Users can switch between eight isolated specialist engines:
- 🩺 **Gastroenterology Expert** — 14 GI sources including casebooks, GLP-1 research, and clinical datasets.
- ❤️ **Cardiology Expert** — 14 cardiovascular sources including ACC/AHA guidelines, ESC protocols, and heart failure studies.
- 💧 **Nephrology Expert** — 13 kidney health sources including KDIGO guidelines, clinical handbooks, and textbook references.
- 🧠 **Neurology Expert** — 12 neuroscience sources including Harrison’s Neurology chapters, WHO neurological disorders, AHA stroke guidelines, and clinical case studies.
- 🩷 **Gynecology Expert** — 12 obstetrics and gynecology sources including WHO guidelines, clinical manuals, and journals.
- 🎗️ **Oncology Expert** — 10 oncology sources including textbooks, manuals, and clinical guidelines.
- 🦴 **Orthopedics Expert** — 8 orthopedic sources including textbooks, clinical examinations, and CPGs.
- 🧓 **Geriatrics Expert** — 7 geriatric sources including WHO ageing guidelines, reference books, and clinical pocketbooks.
=======
*   **Core Engine**: `PageIndex` — Hierarchical, vectorless reasoning RAG.
*   **Orchestration**: `GPT-4o` — High-reasoning LLM for intent analysis and clinical synthesis.
*   **Frontend**: `Streamlit` — Sleek, responsive clinical interface.
*   **Data Integrity**: `LiteLLM` & `PyPDF2` — Standardized API management and local document parsing.
>>>>>>> 848bcc72937d70826d927480a4dc9666f03d2386

---

## 🏥 Clinical Knowledge Repository (14 Sources)

The system is pre-indexed with over **2,500 pages** of elite medical literature, providing a "Deep Context" environment for clinical queries.

| Category | Key Sources | Context Highlights |
| :--- | :--- | :--- |
| **Academic** | *First Principles of GI*, *Yamada's Handbook* | Comprehensive pathophysiology and clinical guidelines. |
| **Research** | *EMJ Journal*, *GLP-1 Peer-Reviewed Studies* | Latest clinical trials and therapeutic breakthroughs (2021-2024). |
| **Clinical** | *Casebook in Gastroenterology* | Protocol-driven case studies and diagnostic logic. |
| **Data** | *GI Disease Dataset*, *CRAN Clinical Sets* | 30,000+ patient record insights and symptomatic mapping. |
| **Nutritional** | *GLP-1 Diet Guides*, *Protein Balance Plans* | Specialized nutritional strategies for GLP-1 therapy. |

---

## 🏗️ Project Blueprint

<<<<<<< HEAD
```
MicroHeal Clinical Bot
├── clinical_engine.py      ← The core brain (import from anywhere)
├── app.py                  ← Streamlit UI (thin skin over the engine)
├── api.py                  ← FastAPI Server (for programmatic requests)
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
├── GynecoRAG/
│   ├── gyneco_agent.py     ← Gyneco wrapper with query_gyneco()
│   ├── index/              ← 12 indexed JSON knowledge files
│   └── data/               ← Source PDFs
├── OncoRAG/
│   ├── onco_agent.py       ← Oncology wrapper with query_onco()
│   ├── index/              ← 10 indexed JSON knowledge files
│   └── data/               ← Source PDFs
├── OrthopedicsRAG/
│   ├── orthopedic_agent.py ← Orthopedic wrapper with query_ortho()
│   ├── index/              ← 8 indexed JSON knowledge files
│   └── data/               ← Source PDFs
├── GeriatricRAG/
│   ├── geriatric_agent.py  ← Geriatrics wrapper with query_geriatric()
│   ├── index/              ← 7 indexed JSON knowledge files
│   └── data/               ← Source PDFs
├── PageIndex/              ← PDF indexing pipeline
├── docs/                   ← Deployment guide
├── logs/                   ← Processing logs
├── Dockerfile
├── requirements.txt
└── .env
=======
A clean, modular structure designed for production stability and easy maintenance.

```text
gastroRAG/
├── PageIndex/
│   ├── app.py                  # 🚀 Main Application (Streamlit UI)
│   ├── gastro_agent_tool.py    # 🧠 Core RAG Engine & Document Registry
│   ├── pageindex/              # 🌲 PageIndex Framework (Vectorless Core)
│   ├── pdfs/                   # 📚 Local Knowledge Vault (14 PDFs)
│   ├── results/                # 🌳 Pre-computed Semantic Trees (JSON)
│   ├── tools/                  # 🛠️ Maintenance & Indexing Utilities
│   │   ├── batch_index_all.py  # Automated multi-PDF indexer
│   │   └── run_pageindex.py    # Single document processing tool
│   ├── logs/                   # 📊 Token usage and system telemetry
│   ├── config.yaml             # ⚙️ Engine parameters & AI settings
│   ├── Dockerfile              # 🐳 Production Container Manifest
│   ├── .dockerignore           # 🛡️ Build Optimization & Security
│   ├── requirements.txt        # Production dependencies
│   └── .env                    # Secure API credentials (Local)
├── docs/                       # 📖 Technical Documentation & Integration Guides
└── README.md                   # 🩺 Project Landing Page
>>>>>>> 848bcc72937d70826d927480a4dc9666f03d2386
```

---

## ⚙️ How It Works: The Clinical Pipeline

GastroRAG follows a rigorous 5-step process to ensure clinical safety and relevance:

1.  **Intent Classification**: Analyzes if a query is medical, administrative, or out-of-scope.
2.  **Terminology Expansion**: Expands medical shorthand (e.g., "GERD") into comprehensive search terms.
3.  **Hierarchical Tree Search**: PageIndex navigates the document "Table of Contents" to find the exact relevant page ranges.
4.  **Evidence Synthesis**: GPT-4o processes the raw retrieved text to form a coherent, professional response.
5.  **Structured Output**: Delivers an **Answer**, followed by **Technical Details**, and a **Clinical Note**.
6.  **Interactive Evidence**: Citations are consolidated into a dedicated **"View Sources & Citations"** UI expander to keep the primary response clean and professional.

---

## 🚀 Deployment & Usage

### 1. Environment Setup
```bash
# Clone the repository
git clone https://github.com/MicroHeal-Wellness/gastroRAG.git
cd gastroRAG/PageIndex

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Credentials
Create a `.env` file in the `PageIndex/` directory:
```env
OPENAI_API_KEY=sk-xxxx-your-clinical-key
```

<<<<<<< HEAD
### 3. Run the Streamlit App (Web UI)
=======
### 3. Launch the Assistant
>>>>>>> 848bcc72937d70826d927480a4dc9666f03d2386
```bash
streamlit run app.py
```

<<<<<<< HEAD
### 4. Run the API Server (For external requests)
```bash
uvicorn api:app --reload
```
You can now send programmatic requests to `http://localhost:8000/query` or view the interactive API docs at `http://localhost:8000/docs`.

### 5. Use in Your Own Code (WhatsApp Bot, API, etc.)
```python
from clinical_engine import ClinicalEngine

# Initialize the specialist you need
gastro = ClinicalEngine("gastro")
cardio = ClinicalEngine("cardio")
nephro = ClinicalEngine("nephro")
neuro = ClinicalEngine("neuro")
gyneco = ClinicalEngine("gyneco")
onco = ClinicalEngine("onco")
ortho = ClinicalEngine("ortho")
geriatric = ClinicalEngine("geriatric")

# Query it
result = gastro.query("What causes GERD?")
print(result["answer"])     # The clinical response
print(result["sources"])    # Real sources (empty if none used)
print(result["out_of_domain"])  # True if wrong specialty

# Geriatrics example
result = geriatric.query("What are the guidelines for integrated care for older people?")
print(result["answer"])

# With conversation history
history = [
    {"role": "user", "content": "What is acid reflux?"},
    {"role": "assistant", "content": "Acid reflux is..."}
]
result = gastro.query("How is it treated?", history=history)
```

---

## 📚 Knowledge Base (73 Indexed Sources)

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

### Gynecology (12 Sources)
| # | Source | Type |
|---|--------|------|
| 1 | WHO Guidelines on Maternal and Newborn Care | Guideline |
| 2 | Obstetrics & Gynecology Clinical Manual | Manual |
| 3 | WHO Safe Abortion Technical & Policy Guidelines | Guideline |
| 4 | WHO Medical Eligibility Criteria for Contraceptive Use | Guideline |
| 5 | WHO Recommendations for Prevention of Postpartum Haemorrhage | Guideline |
| 6 | Obstetrics and Gynecology Structure Reference | Reference |
| 7 | Journal of Clinical Gynecology and Obstetrics | Journal |
| 8 | AIDS Journal: Gynecology Cohort Study | Journal |
| 9 | Journal of Clinical and Reproductive Medicine | Journal |
| 10 | Saudi Journal of Pathology — Gynecological Pathology | Journal |
| 11 | Essential Interventions in Reproductive Health | Guideline |
| 12 | Vanuatu Maternal & Newborn Care Operational Guidance | Manual |

### Oncology (10 Sources)
| # | Source | Type |
|---|--------|------|
| 1 | Dtsch Arztebl Int-120 (445) | Journal |
| 2 | AIDS Journal (37-1871) | Journal |
| 3 | Disease Models & Mechanisms (16-050175) | Research |
| 4 | TBAD017 Clinical Oncology | Journal |
| 5 | WHO Essential Medicines List (EML) 2023 | Reference |
| 6 | Padova Lectures in Oncology | Lectures |
| 7 | Prostate Book 2nd Edition | Textbook |
| 8 | Textbook of Medical Oncology 4th Ed (Cavalli) | Textbook |
| 9 | Oxford Handbook of Oncology 4th Ed | Handbook |
| 10 | The MD Anderson Manual of Medical Oncology 3e | Manual |

### Orthopedics (8 Sources)
| # | Source | Type |
|---|--------|------|
| 1 | Textbook of Orthopedics 4E (John Ebnezar) | Textbook |
| 2 | Clinical Examination in Orthopedics | Textbook |
| 3 | Miller's Review of Orthopedics | Textbook |
| 4 | Orthopedic Principles - A Resident's Guide | Textbook |
| 5 | Chapman's Orthopaedic Surgery | Textbook |
| 6 | CTS CPG | Guideline |
| 7 | OAH CPG | Guideline |
| 8 | OAK3 CPG | Guideline |

### Geriatrics (7 Sources)
| # | Source | Type |
|---|--------|------|
| 1 | Geriatrics/Aging Research Article (41599_2023_Article_1629) | Journal |
| 2 | WHO Integrated Care for Older People (ICOPE) Implementation Framework | Guideline |
| 3 | WHO Global Report on Ageing and Health | Guideline |
| 4 | WHO Guidelines on Integrated Care for Older People | Guideline |
| 5 | Bookshelf Geriatric Care Reference (NBK379406) | Reference |
| 6 | Geriatric Medicine Reference (L-G-0000001100-0002331378) | Reference |
| 7 | NGIG Geriatrics Pocketbook 2025 | Reference |

---

## 🐳 Docker Deployment
=======
### 4. Docker Deployment (Optional)
One container runs a **single server on port 8501** (`server.py` via uvicorn):
- Streamlit UI internally on 8502 (proxied through 8501)
- Retrieval API routes served directly on 8501

| Path | Service |
|------|---------|
| `http://localhost:8501/` | Streamlit UI |
| `POST http://localhost:8501/v1/retrieve` | Retrieval API |
| `GET http://localhost:8501/health` | API health check |
| `http://localhost:8501/docs` | FastAPI Swagger |
>>>>>>> 848bcc72937d70826d927480a4dc9666f03d2386

```bash
# Build and run (docker compose)
docker compose up --build

# Or run the image directly
docker build -t gastrorag:latest .
docker run -p 8501:8501 --env-file .env gastrorag:latest
```

For **agentic-chatbot**, set `GASTRO_RAG_API_URL=http://localhost:8501` (same host/port as Streamlit).

---

## 🔒 Security & Compliance

*   **Data Privacy**: All knowledge retrieval is performed locally against the indexed PDF vault.
*   **No PII**: The system does not store or process Protected Health Information (PHI).
*   **Traceability**: Every response is anchored to a specific clinical source, section, and page range.

---

**GastroRAG** | Built with precision by **MicroHeal Wellness** | Powered by **PageIndex**
