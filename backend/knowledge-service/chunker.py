"""
Document chunking utilities
"""
from typing import List, Dict, Any
import re
from common.config import settings


class TextChunker:
    """Text chunking for RAG"""
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
        separator: str = "\n"
    ):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        self.separator = separator
    
    def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Split text into chunks"""
        chunks = []
        
        # Split by separator
        sentences = re.split(self.separator, text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        current_chunk = ""
        chunk_id = 0
        
        for sentence in sentences:
            # Check if adding this sentence exceeds chunk size
            if len(current_chunk) + len(sentence) + 1 <= self.chunk_size:
                current_chunk += sentence + " "
            else:
                # Save current chunk if not empty
                if current_chunk.strip():
                    chunks.append({
                        "content": current_chunk.strip(),
                        "chunk_id": str(chunk_id),
                        "metadata": metadata or {}
                    })
                    chunk_id += 1
                
                # Start new chunk with overlap
                overlap_text = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else current_chunk
                current_chunk = overlap_text + sentence + " "
        
        # Don't forget the last chunk
        if current_chunk.strip():
            chunks.append({
                "content": current_chunk.strip(),
                "chunk_id": str(chunk_id),
                "metadata": metadata or {}
            })
        
        return chunks
    
    def chunk_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Chunk multiple documents"""
        all_chunks = []
        
        for doc in documents:
            metadata = {
                "document_id": doc.get("id"),
                "filename": doc.get("filename"),
                **doc.get("metadata", {})
            }
            chunks = self.chunk_text(doc["content"], metadata)
            all_chunks.extend(chunks)
        
        return all_chunks


def extract_text_from_file(file_path: str) -> str:
    """Extract text from various file formats"""
    try:
        import PyPDF2
        
        if file_path.endswith('.pdf'):
            text = ""
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return text
        elif file_path.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            # For other formats, try to read as text
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except:
                raise ValueError(f"Unsupported file format: {file_path}")
    except ImportError:
        # If PyPDF2 not available, read as plain text
        if file_path.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            raise ValueError("PyPDF2 is required for PDF processing")
