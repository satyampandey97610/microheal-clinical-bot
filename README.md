# 🩺 GastroRAG: Elite Gastroenterology Clinical Intelligence

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/frontend-streamlit-FF4B4B.svg)](https://streamlit.io/)
[![Engine: PageIndex](https://img.shields.io/badge/engine-PageIndex-000000.svg)](https://github.com/VectifyAI/PageIndex)
[![Model: GPT--4o](https://img.shields.io/badge/llm-GPT--4o-412991.svg)](https://openai.com/)

**GastroRAG** is a production-grade clinical decision support system (CDSS) designed for professional gastroenterologists. Unlike traditional vector-based RAG, it utilizes the **PageIndex** engine to perform reasoning-based retrieval across a high-density clinical knowledge base, ensuring unprecedented accuracy and traceability.

---

## 🛠️ Technology Stack

*   **Core Engine**: `PageIndex` — Hierarchical, vectorless reasoning RAG.
*   **Orchestration**: `GPT-4o` — High-reasoning LLM for intent analysis and clinical synthesis.
*   **Frontend**: `Streamlit` — Sleek, responsive clinical interface.
*   **Data Integrity**: `LiteLLM` & `PyPDF2` — Standardized API management and local document parsing.

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

### 3. Launch the Assistant
```bash
streamlit run app.py
```

### 4. Docker Deployment (Optional)
```bash
# Build the image
docker build -t gastrorag:latest .

# Run the container
docker run -p 8501:8501 --env-file .env gastrorag:latest
```

---

## 🔒 Security & Compliance

*   **Data Privacy**: All knowledge retrieval is performed locally against the indexed PDF vault.
*   **No PII**: The system does not store or process Protected Health Information (PHI).
*   **Traceability**: Every response is anchored to a specific clinical source, section, and page range.

---

**GastroRAG** | Built with precision by **MicroHeal Wellness** | Powered by **PageIndex**
