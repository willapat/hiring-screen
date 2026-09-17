import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import agents.resume_tailor as resume_tailor_agent
from api.deps import get_job_match_graph, get_llm, get_store
from api.review_helpers import build_review_report
from tools.review_models import ReviewReport
from tools.scoring import FitScore, JobAnalysis

router = APIRouter()


class JobMatchRequest(BaseModel):
    resume_id: str
    job_description: str


class JobMatchResponse(BaseModel):
    session_id: str
    status: str
    job_analysis: JobAnalysis | None = None
    fit_score: FitScore | None = None
    message: str | None = None


@router.post("/job-match", response_model=JobMatchResponse)
async def start_job_match(body: JobMatchRequest):
    record = get_store().get(body.resume_id)
    if not record:
        raise HTTPException(status_code=404, detail="Unknown resume_id — it may have expired after a server restart.")

    graph = get_job_match_graph()
    session_id = uuid.uuid4().hex
    config = {"configurable": {"thread_id": session_id}}

    await graph.ainvoke(
        {"job_description": body.job_description, "resume_text": record.extracted.text},
        config=config,
    )

    values = (await graph.aget_state(config)).values

    if not values.get("is_valid"):
        return JobMatchResponse(session_id=session_id, status="rejected", message=values.get("rejection_message"))

    return JobMatchResponse(
        session_id=session_id,
        status="awaiting_review",
        job_analysis=values["job_analysis"],
        fit_score=values["fit_score"],
    )


class AdviceRequest(BaseModel):
    fit_score_override: FitScore | None = None
    note: str | None = None
    tailor: bool = False


class AdviceResponse(BaseModel):
    verdict: str
    advice_markdown: str
    tailoring: ReviewReport | None = None


@router.post("/job-match/{session_id}/advice", response_model=AdviceResponse)
async def get_advice(session_id: str, body: AdviceRequest):
    graph = get_job_match_graph()
    config = {"configurable": {"thread_id": session_id}}

    snapshot = await graph.aget_state(config)
    if not snapshot.values:
        raise HTTPException(status_code=404, detail="Unknown session_id — it may have expired after a server restart.")

    update = {}
    if body.fit_score_override is not None:
        update["fit_score"] = body.fit_score_override
    if body.note:
        update["human_feedback"] = body.note
    if update:
        await graph.aupdate_state(config, update)

    await graph.ainvoke(None, config=config)

    final = (await graph.aget_state(config)).values

    tailoring = None
    if body.tailor:
        text = final["resume_text"]
        issues = resume_tailor_agent.run(get_llm(), text, final["job_analysis"], final["fit_score"])
        tailoring = build_review_report(text, issues)

    return AdviceResponse(verdict=final["fit_score"].verdict, advice_markdown=final["output"], tailoring=tailoring)
