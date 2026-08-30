from typing import Dict, Any, List
from backend.services.embedding_service import EmbeddingService
from backend.services.gemini_service import GeminiService
from backend.database.vector_store import VectorStore

class RAGService:
    """Retrieval-Augmented Generation (RAG) Service."""

    def __init__(self, vector_store: VectorStore, embedding_service: EmbeddingService, gemini_service: GeminiService):
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.gemini_service = gemini_service

    def answer_question(self, question: str, top_k: int = 4) -> Dict[str, Any]:
        """
        Execute full RAG pipeline:
        User Question -> Query Embedding -> Vector Similarity Search -> Top Chunks -> Context Assembly -> Gemini LLM -> Answer + Sources.
        """
        if not question or not question.strip():
            return {
                "answer": "Please ask a valid question.",
                "sources": [],
                "retrieved_chunks": []
            }

        # Step 1 & 2: Generate embedding for question
        query_vector = self.embedding_service.generate_embedding(question)

        # Step 3 & 4: Retrieve top relevant chunks from ChromaDB
        search_results = self.vector_store.search_documents(query_vector, top_k=top_k)

        if not search_results:
            return {
                "answer": "I could not find relevant information in the uploaded documents to answer your question.",
                "sources": [],
                "retrieved_chunks": [],
                "confidence": 0.0
            }

        # Filter out very low relevance results if vector store is populated
        relevant_chunks = [r for r in search_results if r.get("similarity_score", 0.0) >= 0.01]
        if not relevant_chunks:
            relevant_chunks = search_results

        # Extract unique sources
        sources = list(dict.fromkeys([r.get("filename", "unknown") for r in relevant_chunks]))

        # Step 5: Build RAG context string
        context_blocks = []
        for idx, item in enumerate(relevant_chunks):
            source_file = item.get("filename", "unknown")
            text_snippet = item.get("chunk_text", "")
            context_blocks.append(f"[Document Chunk {idx+1} | Source: {source_file}]\n{text_snippet}")

        context_str = "\n\n".join(context_blocks)

        # Step 6: Construct Gemini prompt
        system_instruction = (
            "You are an expert AI Robotics & Autonomous Navigation Assistant. "
            "Your objective is to accurately answer user questions strictly based on the provided retrieved context documents. "
            "CRITICAL RULE: If the answer cannot be deduced from the provided context, state clearly: "
            "'I could not find sufficient information in the uploaded documents to answer this question.' "
            "Do NOT invent or hallucinate facts outside the context."
        )

        prompt = (
            f"--- RETRIEVED KNOWLEDGE CONTEXT ---\n"
            f"{context_str}\n"
            f"--- END OF CONTEXT ---\n\n"
            f"USER QUESTION: {question}\n\n"
            f"Please provide a clear, technical, and precise answer based strictly on the context above."
        )

        # Step 7: Generate answer via Gemini
        answer = self.gemini_service.generate_text(prompt, system_instruction=system_instruction)

        return {
            "answer": answer,
            "sources": sources,
            "retrieved_chunks": relevant_chunks,
            "context_used": context_str,
            "chunk_count": len(relevant_chunks)
        }
