from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agents import resume_reviewer
from api.deps import get_llm, get_store
from api.review_helpers import build_review_report
from tools.review_models import ReviewReport

router = APIRouter()


class ReviewRequest(BaseModel):
    resume_id: str


@router.post("/review", response_model=ReviewReport)
def review_resume(body: ReviewRequest):
    record = get_store().get(body.resume_id)
    if not record:
        raise HTTPException(status_code=404, detail="Unknown resume_id — it may have expired after a server restart.")

    text = record.extracted.text
    issues = resume_reviewer.run(get_llm(), text)
    return build_review_report(text, issues)
