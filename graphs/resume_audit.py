from typing import Optional
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
import agents.resume_reviewer as resume_reviewer_agent
from ats.extract import ExtractedPdf, extract as extract_pdf
from ats.report import scan as scan_ats_report
from tools.ats_models import AtsReport
from tools.review_models import ReviewIssue


class ResumeAuditState(TypedDict):
    resume_path: str
    extracted: Optional[ExtractedPdf]
    ats_report: Optional[AtsReport]
    review_issues: Optional[list[ReviewIssue]]
    health_score: Optional[int]


def build_resume_audit_graph(llm):
    """parse_resume fans out into scan_ats (deterministic) and review_resume
    (one LLM call) running independently — they genuinely don't depend on each
    other — then merge combines them with no further LLM call."""

    def parse_resume(state: ResumeAuditState):
        return {"extracted": extract_pdf(state["resume_path"])}

    def scan_ats(state: ResumeAuditState):
        return {"ats_report": scan_ats_report(state["extracted"])}

    def review_resume(state: ResumeAuditState):
        return {"review_issues": resume_reviewer_agent.run(llm, state["extracted"].text)}

    def merge(state: ResumeAuditState):
        ats_score = state["ats_report"].score
        issue_penalty = min(20, len(state["review_issues"]) * 2)
        health_score = max(0, round(ats_score * 0.8 + (100 - issue_penalty) * 0.2))
        return {"health_score": health_score}

    builder = StateGraph(ResumeAuditState)
    builder.add_node("parse_resume", parse_resume)
    builder.add_node("scan_ats", scan_ats)
    builder.add_node("review_resume", review_resume)
    builder.add_node("merge", merge)

    builder.add_edge(START, "parse_resume")
    builder.add_edge("parse_resume", "scan_ats")
    builder.add_edge("parse_resume", "review_resume")
    builder.add_edge("scan_ats", "merge")
    builder.add_edge("review_resume", "merge")
    builder.add_edge("merge", END)

    return builder.compile()
