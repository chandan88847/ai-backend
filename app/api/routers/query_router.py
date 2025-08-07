from fastapi import APIRouter, Body
from pydantic import BaseModel
from app.services.query_service import answer_query
router = APIRouter(prefix="/query", tags=["Query"])

class QueryRequest(BaseModel):
    question: str
    repo_url: str 


@router.post("/getanswer")
def query_llm(request: QueryRequest):
    """
    Answers a question based on the knowledge base of a specific repository.
    """
    answer = answer_query(
        user_query=request.question,
        repo_url=request.repo_url
    )
    return {"question": request.question, "answer": answer}
