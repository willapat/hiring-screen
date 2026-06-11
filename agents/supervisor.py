import uuid
import base64
from io import BytesIO
from typing import Annotated, Optional
from typing_extensions import TypedDict
from pypdf import PdfReader
from langchain_core.messages import AnyMessage, AIMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
from tools.scoring import JobAnalysis, FitScore
from middleware.guardrails import check as guardrail_check
import agents.job_analyzer as job_analyzer_agent
import agents.fit_scorer as fit_scorer_agent
import agents.interview_prep as interview_prep_agent
import agents.gap_analyzer as gap_analyzer_agent
import agents.role_advisor as role_advisor_agent


class HiringState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    job_description: str
    resume_text: str
    is_valid: Optional[bool]
    job_analysis: Optional[JobAnalysis]
    fit_score: Optional[FitScore]
    human_feedback: Optional[str]
    output: Optional[str]


def _extract_file_text(block: dict) -> str:
    block_type = block.get("type", "")
    if block_type == "document":
        source = block.get("source", {})
        raw = base64.b64decode(source.get("data", "") + "==")
        media_type = source.get("media_type", "")
    elif block_type == "file":
        raw = base64.b64decode(block.get("data", "") + "==")
        media_type = block.get("mime_type", "")
    else:
        return ""
    if "pdf" in media_type:
        reader = PdfReader(BytesIO(raw))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return raw.decode("utf-8", errors="ignore")


def build_graph(llm, checkpointer=None):
    def input_parser(state: HiringState):
        messages = state.get("messages") or []
        last = next((m for m in reversed(messages) if isinstance(m, HumanMessage)), None)
        job_description = ""
        resume_text = ""
        if last:
            content = last.content
            if isinstance(content, str):
                job_description = content
            elif isinstance(content, list):
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") == "text":
                        job_description = block.get("text", "")
                    elif block.get("type") in ("document", "file"):
                        resume_text = _extract_file_text(block)
        if not job_description and not resume_text:
            return {"messages": [AIMessage(content=(
                "Hi! To analyze your job fit, send me one message with:\n\n"
                "1. **Job description** — paste it as your message text\n"
                "2. **Resume** — drag your PDF onto the chat to attach it\n\n"
                "Then hit send."
            ))]}
        if not job_description:
            return {"messages": [AIMessage(content="Please paste the job description as text in your message (along with the resume PDF attached).")]}
        if not resume_text:
            return {"messages": [AIMessage(content="Please also attach your resume PDF — drag it onto the chat input before sending.")]}
        return {"job_description": job_description, "resume_text": resume_text}

    def route_after_parse(state: HiringState) -> str:
        return "validate_input" if state.get("job_description") else END

    def route_start(state: HiringState) -> str:
        return "validate_input" if state.get("job_description") else "input_parser"

    def validate_input(state: HiringState):
        result = guardrail_check(llm, state["job_description"])
        if not result.is_valid:
            return {"is_valid": False, "output": result.message}
        return {"is_valid": True}

    def route_after_validation(state: HiringState) -> str:
        return "analyze_job" if state["is_valid"] else END

    def analyze_job(state: HiringState):
        return {"job_analysis": job_analyzer_agent.run(llm, state["job_description"])}

    def score_fit(state: HiringState):
        return {"fit_score": fit_scorer_agent.run(llm, state["job_analysis"], state["resume_text"])}

    def human_review(state: HiringState):
        fit = state["fit_score"]

        partial_text = ""
        if fit.partial_matches:
            lines = [f"  {m.candidate_has} → {m.required}: {m.note}" for m in fit.partial_matches]
            partial_text = "\nAdjacent skills:\n" + "\n".join(lines)

        display = (
            f"\n{'='*50}\n"
            f"FIT SCORE: {fit.score}/100  ({fit.verdict.upper()})\n"
            f"{'='*50}\n"
            f"Matched:  {', '.join(fit.matched_skills) or 'None'}\n"
            f"Missing:  {', '.join(fit.missing_skills) or 'None'}"
            f"{partial_text}\n\n"
            f"Reasoning: {fit.reasoning}\n"
            f"{'='*50}\n"
            f"If anything looks wrong, type a correction below.\n"
            f"Otherwise press Enter to continue."
        )

        feedback = interrupt(display)
        return {"human_feedback": feedback if feedback and feedback.strip() else None}

    def route_by_verdict(state: HiringState) -> str:
        return state["fit_score"].verdict

    def prep_interview(state: HiringState):
        return {"output": interview_prep_agent.run(
            llm, state["job_analysis"], state["fit_score"], state.get("human_feedback")
        )}

    def analyze_gaps(state: HiringState):
        return {"output": gap_analyzer_agent.run(
            llm, state["job_analysis"], state["fit_score"], state.get("human_feedback")
        )}

    def advise_role(state: HiringState):
        return {"output": role_advisor_agent.run(
            llm, state["job_analysis"], state["fit_score"], state.get("human_feedback")
        )}

    builder = StateGraph(HiringState)

    builder.add_node("input_parser", input_parser)
    builder.add_node("validate_input", validate_input)
    builder.add_node("analyze_job", analyze_job)
    builder.add_node("score_fit", score_fit)
    builder.add_node("human_review", human_review)
    builder.add_node("interview_prep", prep_interview)
    builder.add_node("gap_analyzer", analyze_gaps)
    builder.add_node("role_advisor", advise_role)

    builder.add_conditional_edges(START, route_start, {"input_parser": "input_parser", "validate_input": "validate_input"})
    builder.add_conditional_edges("input_parser", route_after_parse, {"validate_input": "validate_input", END: END})
    builder.add_conditional_edges(
        "validate_input",
        route_after_validation,
        {"analyze_job": "analyze_job", END: END}
    )
    builder.add_edge("analyze_job", "score_fit")
    builder.add_edge("score_fit", "human_review")
    builder.add_conditional_edges(
        "human_review",
        route_by_verdict,
        {
            "strong": "interview_prep",
            "moderate": "gap_analyzer",
            "weak": "role_advisor",
        }
    )
    builder.add_edge("interview_prep", END)
    builder.add_edge("gap_analyzer", END)
    builder.add_edge("role_advisor", END)

    return builder.compile(checkpointer=checkpointer)


def run(llm, job_description: str, resume_text: str) -> str:
    memory = MemorySaver()
    graph = build_graph(llm, checkpointer=memory)
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    initial_state = {
        "messages": [],
        "job_description": job_description,
        "resume_text": resume_text,
        "is_valid": None,
        "job_analysis": None,
        "fit_score": None,
        "human_feedback": None,
        "output": None,
    }

    graph.invoke(initial_state, config=config)

    state = graph.get_state(config).values
    if not state.get("is_valid"):
        raise ValueError(state["output"])

    current = graph.get_state(config)
    if current.next:
        for task in current.tasks:
            for i in task.interrupts:
                print(i.value)
        feedback = input("\n> ").strip()
        graph.invoke(Command(resume=feedback), config=config)

    return graph.get_state(config).values["output"]
