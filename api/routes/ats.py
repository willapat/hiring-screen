from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agents import ats_advisor
from api.deps import get_llm, get_store
from ats.report import scan
from tools.ats_models import AtsReport

router = APIRouter()


class AtsScanRequest(BaseModel):
    resume_id: str
    required_skills: list[str] | None = None
    narrative: bool = True


@router.post("/ats/scan", response_model=AtsReport)
def scan_resume(body: AtsScanRequest):
    record = get_store().get(body.resume_id)
    if not record:
        raise HTTPException(status_code=404, detail="Unknown resume_id — it may have expired after a server restart.")

    report = scan(record.extracted, required_skills=body.required_skills)

    if body.narrative:
        try:
            narrative_markdown = ats_advisor.run(get_llm(), report)
            report = report.model_copy(update={"narrative_markdown": narrative_markdown, "llm_used": True})
        except Exception:
            # The deterministic report is still useful on its own — a narrative
            # failure (quota, network) shouldn't take down the whole response.
            pass

    return report
