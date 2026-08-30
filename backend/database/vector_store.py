import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from backend.utils.config import VECTOR_DB_DIR

COLLECTION_NAME = "vision_navigation_docs"

class VectorStore:
    """Local ChromaDB Vector Database Manager."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_dir = db_path or str(VECTOR_DB_DIR)
        Path(self.db_dir).mkdir(parents=True, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=self.db_dir)
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )

    def add_chunks(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]) -> int:
        """
        Store chunks and their corresponding embeddings into ChromaDB.
        """
        if not chunks or not embeddings or len(chunks) != len(embeddings):
            raise ValueError("Chunks and embeddings must be non-empty and equal in length.")

        ids = [chunk["chunk_id"] for chunk in chunks]
        documents = [chunk["chunk_text"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]

        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        return len(ids)

    def search_documents(self, query_embedding: List[float], top_k: int = 4) -> List[Dict[str, Any]]:
        """
        Perform semantic vector search using query embedding.
        """
        if not query_embedding:
            return []

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, max(1, self.collection.count())) if self.collection.count() > 0 else top_k
        )

        formatted_results = []
        if results and "documents" in results and results["documents"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if "metadatas" in results else [{}] * len(docs)
            distances = results["distances"][0] if "distances" in results and results["distances"] else [0.0] * len(docs)
            ids = results["ids"][0] if "ids" in results else [""] * len(docs)

            for i in range(len(docs)):
                # Convert cosine distance to similarity score
                similarity = round(1.0 - float(distances[i]), 4) if distances else 1.0
                formatted_results.append({
                    "chunk_id": ids[i],
                    "chunk_text": docs[i],
                    "metadata": metas[i],
                    "filename": metas[i].get("filename", "unknown"),
                    "similarity_score": max(0.0, similarity)
                })

        return formatted_results

    def delete_document(self, document_id: str) -> bool:
        """Delete all chunks belonging to a document ID."""
        try:
            results = self.collection.get(where={"doc_id": document_id})
            if results and results["ids"]:
                self.collection.delete(ids=results["ids"])
                return True
            return False
        except Exception as e:
            print(f"Error deleting document {document_id}: {e}")
            return False

    def clear_database(self) -> bool:
        """Clear all entries in the collection."""
        try:
            self.client.delete_collection(COLLECTION_NAME)
            self.collection = self.client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}
            )
            return True
        except Exception as e:
            print(f"Error clearing vector store: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Return vector database metrics."""
        count = self.collection.count()
        return {
            "total_chunks": count,
            "collection_name": COLLECTION_NAME,
            "storage_path": self.db_dir
        }
