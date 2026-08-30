import sys
import site
from pathlib import Path

user_site = site.getusersitepackages()
if user_site not in sys.path:
    sys.path.insert(0, user_site)

import os
import uvicorn

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from backend.utils.config import (
    BASE_DIR, HOST, PORT, is_gemini_key_valid,
    GEMINI_MODEL, GEMINI_EMBEDDING_MODEL, DOCUMENTS_DIR
)
from backend.database.vector_store import VectorStore
from backend.services.gemini_service import GeminiService
from backend.services.embedding_service import EmbeddingService
from backend.services.rag_service import RAGService
from backend.services.vision_service import VisionService
from backend.services.navigation_service import NavigationService
from backend.services.mcp_service import MCPToolService

from backend.routes.chat import router as chat_router, set_rag_service
from backend.routes.documents import router as doc_router, set_document_services, in_memory_docs
from backend.routes.vision import router as vision_router, set_vision_service
from backend.routes.navigation import router as nav_router, set_navigation_services
from backend.utils.document_loader import DocumentLoader
from backend.utils.chunking import IntelligentChunker

app = FastAPI(
    title="Vision-Language Autonomous Navigation System API",
    description="Autonomous Navigation, Vision Perception, Gemini RAG, and MCP Tools",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize core services
vector_store = VectorStore()
gemini_service = GeminiService()
embedding_service = EmbeddingService()
rag_service = RAGService(vector_store, embedding_service, gemini_service)
vision_service = VisionService(gemini_service)
navigation_service = NavigationService(gemini_service, vision_service)
mcp_service = MCPToolService(vector_store, vision_service, navigation_service)

# Wire router dependencies
set_rag_service(rag_service)
set_document_services(vector_store, embedding_service)
set_vision_service(vision_service)
set_navigation_services(navigation_service, vision_service)

# Include API routers
app.include_router(chat_router)
app.include_router(doc_router)
app.include_router(vision_router)
app.include_router(nav_router)

@app.get("/health", tags=["System Health"])
async def health_check():
    """System health check endpoint."""
    key_valid = is_gemini_key_valid()
    stats = vector_store.get_stats()
    return {
        "status": "ok",
        "gemini": key_valid,
        "embeddings": True,
        "chromadb": True,
        "rag": True,
        "vision": True,
        "mcp": True,
        "system": "Vision-Language Autonomous Navigation System",
        "version": "1.0.0",
        "gemini_api_key_configured": key_valid,
        "models": {
            "llm_model": GEMINI_MODEL,
            "embedding_model": GEMINI_EMBEDDING_MODEL
        },
        "components": {
            "gemini_api": "connected" if key_valid else "simulation_mode",
            "embeddings": "ready",
            "vector_database": "ready",
            "rag_engine": "active",
            "vision_system": "ready",
            "navigation_logic": "active",
            "mcp_tools": "ready"
        },
        "vector_db_stats": stats
    }

@app.get("/mcp/tools", tags=["MCP Integration"])
async def list_mcp_tools():
    """Return available Model Context Protocol (MCP) tool schemas."""
    return {"tools": mcp_service.get_tool_definitions()}

@app.post("/mcp/execute", tags=["MCP Integration"])
async def execute_mcp_tool(payload: dict):
    """Execute an MCP tool function."""
    tool_name = payload.get("tool_name", "")
    args = payload.get("arguments", {})
    return mcp_service.execute_tool(tool_name, args)

# Load Demo Sample Document on Startup
@app.on_event("startup")
async def startup_event():
    sample_file = DOCUMENTS_DIR / "sample_navigation.txt"
    if sample_file.exists() and vector_store.collection.count() == 0:
        try:
            doc_id = "doc_sample_01"
            doc_info = DocumentLoader.extract_text(str(sample_file))
            chunker = IntelligentChunker()
            chunks = chunker.create_chunks(doc_info, doc_id)
            if chunks:
                texts = [c["chunk_text"] for c in chunks]
                embeddings = embedding_service.generate_batch_embeddings(texts)
                vector_store.add_chunks(chunks, embeddings)
                in_memory_docs[doc_id] = {
                    "id": doc_id,
                    "filename": "sample_navigation.txt",
                    "saved_filename": "sample_navigation.txt",
                    "extension": ".txt",
                    "char_count": len(doc_info["text"]),
                    "chunk_count": len(chunks),
                    "status": "indexed",
                    "file_size_kb": round(len(doc_info["text"]) / 1024, 2)
                }
                print(f"[STARTUP] Pre-loaded and indexed '{sample_file.name}' with {len(chunks)} chunks.")
        except Exception as e:
            print(f"[STARTUP] Error pre-loading sample doc: {e}")

# Mount static frontend directory
frontend_path = BASE_DIR / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_index():
        return FileResponse(frontend_path / "index.html")

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host=HOST, port=PORT, reload=True)
