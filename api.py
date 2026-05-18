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
