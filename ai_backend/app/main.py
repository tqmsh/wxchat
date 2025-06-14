from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .config import get_settings
from ..services.rag_service import RAGService

app = FastAPI(title="OliverAI Gemini Backend")
settings = get_settings()
rag_service = RAGService(settings)


@app.get("/health")
async def health() -> dict:
    """Basic health check endpoint."""
    return {"status": "ok"}


class DocumentIn(BaseModel):
    course_id: str
    content: str


class QuestionIn(BaseModel):
    course_id: str
    question: str


@app.post("/process_document")
async def process_document(doc: DocumentIn):
    try:
        await rag_service.process_document(doc.course_id, doc.content)
        return {"status": "processed"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/ask")
async def ask_question(data: QuestionIn):
    try:
        answer = await rag_service.answer_question(data.course_id, data.question)
        return {"answer": answer}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
