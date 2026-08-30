import os
from pathlib import Path
from typing import Dict, Any

class DocumentLoader:
    """Document Loader supporting PDF, DOCX, and TXT files."""

    @staticmethod
    def extract_text(file_path: str) -> Dict[str, Any]:
        """
        Extract text from file based on extension.
        Returns dict with filename, extension, text, and page_count.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = path.suffix.lower()
        filename = path.name
        text = ""
        page_count = 1

        if ext == ".pdf":
            text, page_count = DocumentLoader._load_pdf(file_path)
        elif ext == ".docx":
            text = DocumentLoader._load_docx(file_path)
        elif ext in [".txt", ".md", ".log"]:
            text = DocumentLoader._load_txt(file_path)
        else:
            raise ValueError(f"Unsupported file format: '{ext}'. Supported formats: .pdf, .docx, .txt")

        clean_text_content = DocumentLoader._clean_text(text)
        
        return {
            "filename": filename,
            "extension": ext,
            "text": clean_text_content,
            "page_count": page_count,
            "char_count": len(clean_text_content)
        }

    @staticmethod
    def _load_pdf(file_path: str) -> tuple[str, int]:
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            full_text = []
            for page in doc:
                full_text.append(page.get_text())
            doc.close()
            return "\n".join(full_text), len(doc)
        except Exception as e:
            raise RuntimeError(f"Error parsing PDF file with PyMuPDF: {str(e)}")

    @staticmethod
    def _load_docx(file_path: str) -> str:
        try:
            import docx
            doc = docx.Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n".join(paragraphs)
        except Exception as e:
            raise RuntimeError(f"Error parsing DOCX file: {str(e)}")

    @staticmethod
    def _load_txt(file_path: str) -> str:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            raise RuntimeError(f"Error reading TXT file: {str(e)}")

    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean and normalize raw extracted text."""
        if not text:
            return ""
        # Remove null characters and normalize white space lines
        lines = [line.strip() for line in text.splitlines()]
        cleaned = "\n".join(line for line in lines if line)
        return cleaned
