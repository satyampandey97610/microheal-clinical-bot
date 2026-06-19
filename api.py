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

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "MicroHeal Clinical Bot API is running."}

import re

def format_for_whatsapp(text: str) -> str:
    if not text:
        return text
    # 1. Convert markdown headers (# Header or ## Header) to WhatsApp bold: *Header*
    text = re.sub(r'^#+\s+(.*?)$', r'*\1*', text, flags=re.MULTILINE)
    # 2. Convert markdown bold with colons: **Text**: -> *Text:* (bolds correctly on WhatsApp)
    text = re.sub(r'\*\*(.*?)\*\*:', r'*\1:*', text)
    # 3. Convert standard markdown bold: **Text** -> *Text*
    text = re.sub(r'\*\*(.*?)\*\*', r'*\1*', text)
    # 4. Convert single asterisk bold with colons: *Text*: -> *Text:*
    text = re.sub(r'\*(.*?)\*:', r'*\1:*', text)
    # 5. Convert list bullets (-, *, ·, •) to standard WhatsApp bullet (•)
    text = re.sub(r'^\s*[-*·]\s+', r'• ', text, flags=re.MULTILINE)
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
