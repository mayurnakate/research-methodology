"""
Document Parser and Manuscript Chunking Module
Extracts text from files (TXT, MD, DOCX, TEX) and partitions
manuscripts into logical semantic chunks for Merkle Tree construction.
Author: Mayur Sanjay Nakate
"""

import io
import re
from typing import List, Dict, Any, Tuple


class DocumentParser:
    """Parses and partitions academic manuscripts into verifiable chunks."""

    @staticmethod
    def extract_text(file_bytes: bytes, filename: str) -> str:
        """Extract text from file bytes depending on file extension."""
        ext = filename.lower().split(".")[-1] if "." in filename else "txt"

        if ext in ("txt", "md", "tex", "csv", "json", "py"):
            try:
                return file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                return file_bytes.decode("latin-1", errors="replace")

        elif ext == "docx":
            try:
                import docx
                doc = docx.Document(io.BytesIO(file_bytes))
                paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
                return "\n\n".join(paragraphs)
            except Exception as e:
                # Fallback if docx fails
                return f"[DOCX Extraction Fallback: {len(file_bytes)} bytes]"

        else:
            # Fallback for other formats
            try:
                return file_bytes.decode("utf-8", errors="replace")
            except Exception:
                return str(file_bytes[:1000])

    @staticmethod
    def chunk_manuscript(text: str, chunk_mode: str = "paragraphs", min_chunk_words: int = 25) -> List[Dict[str, Any]]:
        """
        Split manuscript text into logical chunks.
        chunk_mode: 'paragraphs' (by double newline) or 'fixed_size' (by word count).
        Returns list of dicts with chunk_id, title/header, word_count, and text.
        """
        raw_chunks: List[str] = []

        if chunk_mode == "paragraphs":
            # Split by double newlines or major section headers
            parts = re.split(r'\n\s*\n', text)
            current_buffer = []
            current_word_count = 0

            for p in parts:
                cleaned = p.strip()
                if not cleaned:
                    continue
                words = len(cleaned.split())
                if current_word_count + words < min_chunk_words and current_buffer:
                    current_buffer.append(cleaned)
                    current_word_count += words
                else:
                    if current_buffer:
                        raw_chunks.append("\n\n".join(current_buffer))
                    current_buffer = [cleaned]
                    current_word_count = words

            if current_buffer:
                raw_chunks.append("\n\n".join(current_buffer))

        else:
            # Fixed word chunking
            words = text.split()
            step = max(50, min_chunk_words)
            for i in range(0, len(words), step):
                raw_chunks.append(" ".join(words[i:i + step]))

        if not raw_chunks:
            raw_chunks = [text if text.strip() else "Empty manuscript placeholder"]

        chunks_with_metadata = []
        for i, chunk in enumerate(raw_chunks):
            # Extract possible title / first line
            first_line = chunk.strip().split("\n")[0][:60]
            title = f"Chunk #{i+1}: {first_line}" if len(first_line) > 3 else f"Chunk #{i+1} [Offset {i*50}]"
            chunks_with_metadata.append({
                "chunk_id": i,
                "title": title,
                "text": chunk,
                "word_count": len(chunk.split()),
                "char_count": len(chunk)
            })

        return chunks_with_metadata
