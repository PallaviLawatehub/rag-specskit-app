import re
from typing import List, Tuple


def extract_text(file_path: str) -> str:
    """Extract text from .txt, .md, or .pdf files."""
    if file_path.endswith(".pdf"):
        # Simple PDF support via PyPDF2 (optional)
        try:
            import PyPDF2
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                # Some pages may return None from extract_text(); filter those
                parts = []
                for page in reader.pages:
                    p = page.extract_text()
                    if p:
                        parts.append(p)
                text = "\n".join(parts)
                return text
        except ImportError:
            raise RuntimeError("PyPDF2 not installed for PDF support")
    else:
        # .txt, .md
        # Try UTF-8 first, then fall back to latin1 or ignore errors
        for encoding in ["utf-8", "latin1", "utf-8-sig"]:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    return f.read()
            except (UnicodeDecodeError, LookupError):
                continue
        # Final fallback: read as UTF-8 and ignore decode errors
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Split text into overlapping chunks.
    Args:
        text: Input text
        chunk_size: Target chunk size in characters
        overlap: Overlap between consecutive chunks in characters
    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end]
        chunks.append(chunk.strip())
        start = end - overlap if end < len(text) else len(text)
    return [c for c in chunks if c]  # Filter empty chunks
