import re
from typing import List, Dict, Any

class IntelligentChunker:
    """
    Intelligent text chunker targeting 800–1200 characters (~200-300 words / tokens)
    with 100–200 character overlap, respecting paragraph and sentence boundaries.
    """

    def __init__(self, target_chunk_size: int = 1000, overlap: int = 150):
        self.target_chunk_size = target_chunk_size
        self.overlap = overlap

    def create_chunks(self, document_info: Dict[str, Any], doc_id: str) -> List[Dict[str, Any]]:
        text = document_info.get("text", "")
        filename = document_info.get("filename", "unknown")
        
        if not text.strip():
            return []

        # Split into paragraphs first
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
        
        raw_chunks = []
        current_chunk = []
        current_length = 0

        for paragraph in paragraphs:
            para_len = len(paragraph)
            
            if current_length + para_len > self.target_chunk_size and current_chunk:
                raw_chunks.append("\n\n".join(current_chunk))
                # Keep overlap from paragraph end
                overlap_text = current_chunk[-1] if current_chunk else ""
                current_chunk = [overlap_text, paragraph] if len(overlap_text) < self.overlap else [paragraph]
                current_length = sum(len(p) for p in current_chunk)
            else:
                current_chunk.append(paragraph)
                current_length += para_len

        if current_chunk:
            raw_chunks.append("\n\n".join(current_chunk))

        # Sentence-based fallback split if any chunk exceeds 1500 chars
        final_chunks = []
        for idx, chunk_text in enumerate(raw_chunks):
            if len(chunk_text) > 1500:
                sentences = re.split(r'(?<=[.!?])\s+', chunk_text)
                sub_chunk = []
                sub_len = 0
                for sent in sentences:
                    if sub_len + len(sent) > self.target_chunk_size and sub_chunk:
                        final_chunks.append(" ".join(sub_chunk))
                        sub_chunk = [sent]
                        sub_len = len(sent)
                    else:
                        sub_chunk.append(sent)
                        sub_len += len(sent)
                if sub_chunk:
                    final_chunks.append(" ".join(sub_chunk))
            else:
                final_chunks.append(chunk_text)

        # Build chunk objects with metadata
        chunk_objects = []
        for i, chunk_text in enumerate(final_chunks):
            chunk_id = f"{doc_id}_chunk_{i+1}"
            chunk_objects.append({
                "chunk_id": chunk_id,
                "document_id": doc_id,
                "filename": filename,
                "chunk_index": i + 1,
                "total_chunks": len(final_chunks),
                "chunk_text": chunk_text,
                "char_length": len(chunk_text),
                "metadata": {
                    "doc_id": doc_id,
                    "filename": filename,
                    "chunk_index": i + 1,
                    "total_chunks": len(final_chunks),
                    "source": filename
                }
            })

        return chunk_objects
