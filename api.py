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

@app.post("/query", response_model=QueryResponse)
def query_bot(request: QueryRequest):
    """
    Query the MicroHeal Clinical Bot.
    - **domain**: 'gastro', 'cardio', 'nephro', 'neuro', or 'gyneco'
    - **query**: The clinical question.
    - **history**: (Optional) List of previous messages in the conversation.
    """
    try:
        engine = get_engine(request.domain)
        history_dicts = [{"role": msg.role, "content": msg.content} for msg in request.history]
        
        result = engine.query(request.query, history=history_dicts)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
