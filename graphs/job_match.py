from typing import Optional
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from tools.scoring import JobAnalysis, FitScore
from middleware.guardrails import check as guardrail_check
import agents.job_analyzer as job_analyzer_agent
import agents.fit_scorer as fit_scorer_agent
import agents.interview_prep as interview_prep_agent
import agents.gap_analyzer as gap_analyzer_agent
import agents.role_advisor as role_advisor_agent


class JobMatchState(TypedDict):
    job_description: str
    resume_text: str
    is_valid: Optional[bool]
    rejection_message: Optional[str]
    job_analysis: Optional[JobAnalysis]
    fit_score: Optional[FitScore]
    human_feedback: Optional[str]
    output: Optional[str]


def build_job_match_graph(llm, checkpointer=None, pause_for_review: bool = True):
    def validate_input(state: JobMatchState):
        result = guardrail_check(llm, state["job_description"])
        if not result.is_valid:
            return {"is_valid": False, "rejection_message": result.message}
        return {"is_valid": True}

    def route_after_validation(state: JobMatchState) -> str:
        return "analyze_job" if state["is_valid"] else END

    def analyze_job(state: JobMatchState):
        return {"job_analysis": job_analyzer_agent.run(llm, state["job_description"])}

    def score_fit(state: JobMatchState):
        return {"fit_score": fit_scorer_agent.run(llm, state["job_analysis"], state["resume_text"])}

    def route_by_verdict(state: JobMatchState) -> str:
        return state["fit_score"].verdict

    def prep_interview(state: JobMatchState):
        output = interview_prep_agent.run(llm, state["job_analysis"], state["fit_score"], state.get("human_feedback"))
        return {"output": output}

    def analyze_gaps(state: JobMatchState):
        output = gap_analyzer_agent.run(llm, state["job_analysis"], state["fit_score"], state.get("human_feedback"))
        return {"output": output}

    def advise_role(state: JobMatchState):
        output = role_advisor_agent.run(llm, state["job_analysis"], state["fit_score"], state.get("human_feedback"))
        return {"output": output}

    builder = StateGraph(JobMatchState)
    builder.add_node("validate_input", validate_input)
    builder.add_node("analyze_job", analyze_job)
    builder.add_node("score_fit", score_fit)
    builder.add_node("interview_prep", prep_interview)
    builder.add_node("gap_analyzer", analyze_gaps)
    builder.add_node("role_advisor", advise_role)

    builder.add_edge(START, "validate_input")
    builder.add_conditional_edges(
        "validate_input", route_after_validation, {"analyze_job": "analyze_job", END: END}
    )
    builder.add_edge("analyze_job", "score_fit")
    builder.add_conditional_edges(
        "score_fit",
        route_by_verdict,
        {"strong": "interview_prep", "moderate": "gap_analyzer", "weak": "role_advisor"},
    )
    builder.add_edge("interview_prep", END)
    builder.add_edge("gap_analyzer", END)
    builder.add_edge("role_advisor", END)

    interrupt_after = ["score_fit"] if pause_for_review else []
    return builder.compile(checkpointer=checkpointer, interrupt_after=interrupt_after)
