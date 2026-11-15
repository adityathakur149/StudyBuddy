from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import uvicorn
from rag_service import RAGService

app = FastAPI(
    title="StudyBuddy AI — RAG API",
    description="Backend API for RAG-powered PDF question answering and study assistance",
    version="1.0.0"
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rag_service = RAGService()

class QueryRequest(BaseModel):
    question: str
    collection_name: Optional[str] = "default"
    top_k: Optional[int] = 3

class QueryResponse(BaseModel):
    question: str
    answer: str
    citations: List[dict]
    retrieval_score: float

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "StudyBuddy AI RAG API",
        "version": "1.0.0"
    }

@app.post("/api/upload", summary="Upload and ingest PDF document")
async def upload_pdf(file: UploadFile = File(...), collection_name: str = Form("default")):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    upload_dir = os.path.join(os.path.dirname(__file__), "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
        
    result = await rag_service.ingest_pdf(file_path, collection_name=collection_name)
    return result

@app.post("/api/query", response_model=QueryResponse, summary="Ask a question over ingested study material")
async def query_study_material(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
        
    response = await rag_service.query(
        question=request.question,
        collection_name=request.collection_name,
        top_k=request.top_k
    )
    return response

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
