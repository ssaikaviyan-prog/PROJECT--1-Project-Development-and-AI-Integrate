import os
import uuid
from pathlib import Path
from typing import List, Dict, Any
from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.utils.config import DOCUMENTS_DIR
from backend.utils.document_loader import DocumentLoader
from backend.utils.chunking import IntelligentChunker

router = APIRouter(prefix="/documents", tags=["Document Analyzer & Vector Store"])

# Service references
vector_store = None
embedding_service = None
chunker = IntelligentChunker(target_chunk_size=1000, overlap=150)
in_memory_docs: Dict[str, Dict[str, Any]] = {}

def set_document_services(v_store, e_service):
    global vector_store, embedding_service
    vector_store = v_store
    embedding_service = e_service

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not vector_store or not embedding_service:
        raise HTTPException(status_code=500, detail="Document storage services are not initialized.")

    if not file.filename:
        raise HTTPException(status_code=400, detail="Invalid file uploaded.")

    # Validate file format
    ext = Path(file.filename).suffix.lower()
    if ext not in [".pdf", ".docx", ".txt"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{ext}'. Allowed extensions are: .pdf, .docx, .txt"
        )

    doc_id = f"doc_{uuid.uuid4().hex[:8]}"
    saved_path = DOCUMENTS_DIR / f"{doc_id}_{file.filename}"

    try:
        # Save file to disk
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        with open(saved_path, "wb") as f:
            f.write(contents)

        # Step 1: Extract Text
        doc_info = DocumentLoader.extract_text(str(saved_path))
        
        # Step 2: Intelligent Chunking
        chunks = chunker.create_chunks(doc_info, doc_id=doc_id)
        if not chunks:
            raise HTTPException(status_code=400, detail="No readable text content found in document.")

        # Step 3: Generate Gemini Embeddings
        chunk_texts = [c["chunk_text"] for c in chunks]
        embeddings = embedding_service.generate_batch_embeddings(chunk_texts)

        # Step 4: Store Vectors in ChromaDB
        added_count = vector_store.add_chunks(chunks, embeddings)

        # Track document metadata
        doc_metadata = {
            "id": doc_id,
            "filename": file.filename,
            "saved_filename": saved_path.name,
            "extension": ext,
            "char_count": len(doc_info["text"]),
            "chunk_count": len(chunks),
            "status": "indexed",
            "file_size_kb": round(len(contents) / 1024, 2)
        }
        in_memory_docs[doc_id] = doc_metadata

        return {
            "message": "Document uploaded and indexed successfully into vector database.",
            "document": doc_metadata
        }

    except Exception as e:
        if saved_path.exists():
            os.remove(saved_path)
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")

@router.get("")
async def list_documents():
    """List all indexed documents and vector DB stats."""
    stats = vector_store.get_stats() if vector_store else {}
    return {
        "documents": list(in_memory_docs.values()),
        "total_documents": len(in_memory_docs),
        "vector_store": stats
    }

@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document by document ID."""
    if doc_id not in in_memory_docs:
        raise HTTPException(status_code=404, detail="Document ID not found.")

    doc_info = in_memory_docs[doc_id]
    if vector_store:
        vector_store.delete_document(doc_id)

    # Remove physical file
    saved_file = DOCUMENTS_DIR / doc_info["saved_filename"]
    if saved_file.exists():
        os.remove(saved_file)

    del in_memory_docs[doc_id]
    return {"message": f"Document '{doc_info['filename']}' deleted successfully."}

@router.post("/clear")
async def clear_database():
    """Clear all vector database entries."""
    if vector_store:
        vector_store.clear_database()
    in_memory_docs.clear()
    
    # Remove files in documents directory
    for item in DOCUMENTS_DIR.glob("*"):
        if item.is_file():
            os.remove(item)

    return {"message": "Vector database and document store cleared completely."}
