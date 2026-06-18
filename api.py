<<<<<<< HEAD
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
from clinical_engine import ClinicalEngine, DOMAIN_CONFIG

app = FastAPI(
    title="MicroHeal Clinical Bot API",
    description="API for programmatically querying the MicroHeal Clinical Bot",
    version="1.0.0"
)

# Cache for engines so we don't reload them on every request
engines = {}

def get_engine(domain: str) -> ClinicalEngine:
    domain = domain.lower().strip()
    if domain not in DOMAIN_CONFIG:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid domain '{domain}'. Allowed domains are: {', '.join(DOMAIN_CONFIG.keys())}."
        )
    if domain not in engines:
        engines[domain] = ClinicalEngine(domain)
    return engines[domain]

class Message(BaseModel):
    role: str
    content: str

class QueryRequest(BaseModel):
    domain: str
    query: str
    history: Optional[List[Message]] = []

class SourceItem(BaseModel):
    source: str
    type: str
    title: str
    content: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceItem]
    domain: str
    out_of_domain: bool

@app.get("/")
def health_check():
    return {"status": "ok", "message": "MicroHeal Clinical Bot API is running."}

import re

def format_for_whatsapp(text: str) -> str:
    if not text:
        return text
    # 1. Convert markdown bold with colons: **Text**: -> *Text:* (bolds correctly on WhatsApp)
    text = re.sub(r'\*\*(.*?)\*\*:', r'*\1:*', text)
    # 2. Convert standard markdown bold: **Text** -> *Text*
    text = re.sub(r'\*\*(.*?)\*\*', r'*\1*', text)
    # 3. Convert single asterisk bold with colons: *Text*: -> *Text:*
    text = re.sub(r'\*(.*?)\*:', r'*\1:*', text)
    # 4. Convert list bullets (-, *, ·, •) to standard WhatsApp bullet (•)
    text = re.sub(r'^\s*[-*·•]\s+', r'• ', text, flags=re.MULTILINE)
    return text

@app.post("/query", response_model=QueryResponse)
def query_bot(request: QueryRequest):
    """
    Query the MicroHeal Clinical Bot.
    - **domain**: 'gastro', 'cardio', 'nephro', 'neuro', 'gyneco', 'onco', 'ortho', or 'geriatric'
    - **query**: The clinical question.
    - **history**: (Optional) List of previous messages in the conversation.
    """
    try:
        engine = get_engine(request.domain)
        history_dicts = [{"role": msg.role, "content": msg.content} for msg in request.history]
        
        result = engine.query(request.query, history=history_dicts)
        # Format the generated answer specifically for WhatsApp compatibility
        result["answer"] = format_for_whatsapp(result["answer"])
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
=======
"""
GastroRAG HTTP API — retrieval over pre-indexed PageIndex JSON trees.
"""
from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from retrieval import RESULTS_DIR, count_documents_loaded, retrieve

# retrieval._load_env() runs on import and loads RAG-Microheal / parent .env files

RAG_API_KEY = os.getenv("RAG_API_KEY", "").strip()

app = FastAPI(
    title="GastroRAG API",
    description="Retrieval service for Microheal gastro knowledge (PageIndex JSON trees).",
    version="1.0.0",
)


def _verify_api_key(x_api_key: Optional[str] = Header(default=None)) -> None:
    if not RAG_API_KEY:
        return
    if x_api_key != RAG_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key")


class RetrieveRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4000)
    top_k: int = Field(default=6, ge=1, le=12)
    use_llm_ranking: bool = Field(default=True)


class ChunkOut(BaseModel):
    source: str
    doc_type: str
    title: str
    content: str
    score: float = 0.0


class RankingMeta(BaseModel):
    expanded_query: str
    candidate_count: int
    selected_count: int


class RetrieveResponse(BaseModel):
    found: bool
    query: str
    use_llm_ranking: bool
    chunks: List[ChunkOut]
    context: Optional[str] = None
    latency_ms: int
    ranking: RankingMeta


@app.get("/health")
def health() -> Dict[str, Any]:
    loaded = count_documents_loaded()
    return {
        "status": "ok" if loaded > 0 else "degraded",
        "documents_loaded": loaded,
        "results_dir": str(RESULTS_DIR),
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
    }


@app.post("/v1/retrieve", response_model=RetrieveResponse, dependencies=[Depends(_verify_api_key)])
def retrieve_v1(body: RetrieveRequest) -> RetrieveResponse:
    if not RESULTS_DIR.is_dir():
        raise HTTPException(status_code=503, detail=f"Results directory not found: {RESULTS_DIR}")

    if body.use_llm_ranking and not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY is required when use_llm_ranking=true",
        )

    t0 = time.perf_counter()
    try:
        result = retrieve(
            query=body.query,
            top_k=body.top_k,
            use_llm_ranking=body.use_llm_ranking,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {e}") from e

    latency_ms = int((time.perf_counter() - t0) * 1000)

    chunks_out = [ChunkOut(**c) for c in result["chunks"]]

    return RetrieveResponse(
        found=result["found"],
        query=body.query,
        use_llm_ranking=body.use_llm_ranking,
        chunks=chunks_out,
        context=result["context"],
        latency_ms=latency_ms,
        ranking=RankingMeta(
            expanded_query=result["expanded_query"],
            candidate_count=result["candidate_count"],
            selected_count=result["selected_count"],
        ),
    )
>>>>>>> 848bcc72937d70826d927480a4dc9666f03d2386
