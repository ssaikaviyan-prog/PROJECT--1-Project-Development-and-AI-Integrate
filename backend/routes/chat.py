from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ChatRequest(BaseModel):
    message: str
    top_k: Optional[int] = 4

class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
    retrieved_chunks: List[Dict[str, Any]]

router = APIRouter(prefix="/chat", tags=["Chat & RAG Assistant"])

# Dependencies will be set during main app initialization
rag_service = None

def set_rag_service(service):
    global rag_service
    rag_service = service

@router.post("", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    if not rag_service:
        raise HTTPException(status_code=500, detail="RAG Service is not initialized.")

    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message content cannot be empty.")

    try:
        result = rag_service.answer_question(request.message, top_k=request.top_k or 4)
        return ChatResponse(
            answer=result.get("answer", ""),
            sources=result.get("sources", []),
            retrieved_chunks=result.get("retrieved_chunks", [])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing error: {str(e)}")
