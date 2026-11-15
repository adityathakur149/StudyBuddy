import os
import fitz  # PyMuPDF
from typing import List, Dict, Any

def split_text_recursive(text: str, chunk_size: int = 500, chunk_overlap: int = 200) -> List[str]:
    """Pure-Python recursive character text splitter (no external deps)."""
    if len(text) <= chunk_size:
        return [text]
    
    separators = ["\n\n", "\n", " ", ""]
    
    def _split(text: str, seps: List[str]) -> List[str]:
        if not seps:
            return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        
        sep = seps[0]
        parts = text.split(sep)
        if len(parts) == 1:
            return _split(text, seps[1:])
        
        chunks = []
        current = ""
        for part in parts:
            candidate = current + (sep if current else "") + part
            if len(candidate) <= chunk_size:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                if len(part) > chunk_size:
                    chunks.extend(_split(part, seps[1:]))
                else:
                    current = part
        if current:
            chunks.append(current)
        return chunks
    
    initial_chunks = _split(text, separators)
    
    # Apply overlap
    if chunk_overlap > 0 and len(initial_chunks) > 1:
        overlapped = []
        for i, chunk in enumerate(initial_chunks):
            if i == 0:
                overlapped.append(chunk)
            else:
                prev = initial_chunks[i-1]
                overlap_text = prev[-chunk_overlap:] if len(prev) > chunk_overlap else prev
                overlapped.append(overlap_text + chunk)
        return overlapped
    return initial_chunks


class RAGService:
    def __init__(self, vector_db_dir: str = "chroma_db"):
        self.vector_db_dir = os.path.join(os.path.dirname(__file__), vector_db_dir)
        os.makedirs(self.vector_db_dir, exist_ok=True)
        
        # In-memory document storage fallback
        self.documents_store: Dict[str, List[Dict[str, Any]]] = {}

    def extract_text_from_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract text from PDF pages with page number citations."""
        doc = fitz.open(pdf_path)
        pages_content = []
        filename = os.path.basename(pdf_path)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            if text.strip():
                pages_content.append({
                    "page_number": page_num + 1,
                    "text": text.strip(),
                    "source": filename
                })
        return pages_content

    async def ingest_pdf(self, pdf_path: str, collection_name: str = "default") -> Dict[str, Any]:
        """Ingest PDF, split into semantic chunks, and store in vector repository."""
        pages = self.extract_text_from_pdf(pdf_path)
        chunks = []
        
        for page in pages:
            page_chunks = split_text_recursive(page["text"], chunk_size=500, chunk_overlap=200)
            for chunk in page_chunks:
                chunks.append({
                    "text": chunk,
                    "metadata": {
                        "source": page["source"],
                        "page_number": page["page_number"]
                    }
                })
                
        if collection_name not in self.documents_store:
            self.documents_store[collection_name] = []
            
        self.documents_store[collection_name].extend(chunks)
        
        return {
            "status": "success",
            "filename": os.path.basename(pdf_path),
            "pages_extracted": len(pages),
            "chunks_created": len(chunks),
            "collection": collection_name
        }

    async def query(self, question: str, collection_name: str = "default", top_k: int = 3) -> Dict[str, Any]:
        """Perform semantic search retrieval and context generation."""
        chunks = self.documents_store.get(collection_name, [])
        
        if not chunks:
            return {
                "question": question,
                "answer": "No documents uploaded yet. Please upload study materials to get answers.",
                "citations": [],
                "retrieval_score": 0.0
            }

        # Simple keyword matching fallback score
        words = set(question.lower().split())
        scored_chunks = []
        
        for chunk in chunks:
            chunk_words = set(chunk["text"].lower().split())
            overlap = len(words.intersection(chunk_words))
            score = overlap / max(len(words), 1)
            scored_chunks.append((score, chunk))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_chunks = [c for _, c in scored_chunks[:top_k]]

        if not top_chunks or scored_chunks[0][0] == 0:
            context = "Context from uploaded materials:\n" + "\n".join([f"- {c['text']}" for c in chunks[:top_k]])
        else:
            context = "Relevant context from uploaded materials:\n" + "\n".join([f"- {c['text']}" for c in top_chunks])

        citations = [
            {
                "source": c["metadata"]["source"],
                "page_number": c["metadata"]["page_number"],
                "snippet": c["text"][:150] + "..."
            }
            for c in top_chunks
        ]

        answer = f"Based on your study notes:\n{top_chunks[0]['text'] if top_chunks else 'No direct match found.'}"

        return {
            "question": question,
            "answer": answer,
            "citations": citations,
            "retrieval_score": round(scored_chunks[0][0] if scored_chunks else 0.0, 2)
        }
