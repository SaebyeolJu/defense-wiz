from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.qa_service import qa_service

router = APIRouter()

class QuestionRequest(BaseModel):
    question: str
    limit: Optional[int] = 5

class QAResponse(BaseModel):
    answer: str

@router.post("/ask", response_model=QAResponse)
async def ask_question(request: QuestionRequest):
    answer = await qa_service.ask_question(request.question)
    return QAResponse(answer=answer)
