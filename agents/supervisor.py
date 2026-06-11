import os
import uuid
from typing import Annotated, Optional
from typing_extensions import TypedDict
from langchain_core.messages import AnyMessage, AIMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
from tools.scoring import JobAnalysis, FitScore
from tools.file_tools import read_resume
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


def _latest_user_text(messages: list) -> str:
    """Pull the plain text out of the most recent human message."""
    last = next((m for m in reversed(messages) if isinstance(m, HumanMessage)), None)
    if not last:
        return ""
    content = last.content
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                return block.get("text", "").strip()
    return ""


def build_graph(llm, checkpointer=None):
    def input_parser(state: HiringState):
        text = _latest_user_text(state.get("messages") or [])

        # Step 1 — collect the job description.
        if not state.get("job_description"):
            if not text:
                return {"messages": [AIMessage(content=(
                    "Hi! I analyze how well you fit a job — I score your match against "
                    "the required skills, then give you tailored advice (interview prep, "
                    "skill gaps, or better-fit roles, depending on the score).\n\n"
                    "To start, **paste the full job description** as your message and hit send."
                ))]}
            check = guardrail_check(llm, text)
            if not check.is_valid:
                return {"messages": [AIMessage(content=(
                    "Hi there! 👋 I'm a job-fit assistant. Here's what I do:\n\n"
                    "I take a job posting and your resume, score how well you match the "
                    "required skills (0–100), and then give you tailored advice — interview "
                    "prep if you're a strong fit, a skill-gap plan if you're close, or "
                    "better-fit role suggestions if it's a stretch.\n\n"
                    "That message didn't look like a job posting, though — to get started, "
                    "**paste the full job description** as your message and hit send."
                ))]}
            return {
                "job_description": text,
                "is_valid": True,
                "messages": [AIMessage(content=(
                    "Got the job description. ✅\n\n"
                    "Now send me your **resume**, either way works:\n"
                    "- the **file path** to it — e.g. `/Users/willpatton/resume.pdf`, or\n"
                    "- **paste the resume text** directly.\n\n"
                    "Then hit send and I'll run the analysis."
                ))],
            }

        # Step 2 — collect the resume (file path or pasted text).
        if not state.get("resume_text"):
            if not text:
                return {"messages": [AIMessage(content="Please send your resume — a file path or pasted text.")]}
            candidate = os.path.expanduser(text.strip().strip("'\""))
            if os.path.exists(candidate):
                try:
                    resume_text = read_resume(candidate)
                except (ValueError, FileNotFoundError) as e:
                    return {"messages": [AIMessage(content=(
                        f"I couldn't read that file: {e}\n\nTry pasting the resume text instead."
                    ))]}
            else:
                resume_text = text
            return {"resume_text": resume_text}

        return {}

    def route_after_parse(state: HiringState) -> str:
        if state.get("job_description") and state.get("resume_text"):
            return "validate_input"
        return END

    def route_start(state: HiringState) -> str:
        if state.get("job_description") and state.get("resume_text"):
            return "validate_input"
        return "input_parser"

    def validate_input(state: HiringState):
        if state.get("is_valid"):
            return {}
        result = guardrail_check(llm, state["job_description"])
        if not result.is_valid:
            return {"is_valid": False, "output": result.message}
        return {"is_valid": True}

    def route_after_validation(state: HiringState) -> str:
        return "analyze_job" if state["is_valid"] else END

    def analyze_job(state: HiringState):
        return {"job_analysis": job_analyzer_agent.run(llm, state["job_description"])}

    def score_fit(state: HiringState):
        fit = fit_scorer_agent.run(llm, state["job_analysis"], state["resume_text"])

        partial_text = ""
        if fit.partial_matches:
            lines = [f"- {m.candidate_has} → {m.required}: {m.note}" for m in fit.partial_matches]
            partial_text = "\n\n**Adjacent skills:**\n" + "\n".join(lines)

        summary = (
            f"### Fit Score: {fit.score}/100 — {fit.verdict.upper()}\n\n"
            f"**Matched:** {', '.join(fit.matched_skills) or 'None'}\n\n"
            f"**Missing:** {', '.join(fit.missing_skills) or 'None'}"
            f"{partial_text}\n\n"
            f"**Reasoning:** {fit.reasoning}"
        )

        return {"fit_score": fit, "messages": [AIMessage(content=summary)]}

    def human_review(state: HiringState):
        feedback = interrupt(
            "If anything in the fit score looks wrong, type a correction. "
            "Otherwise send an empty message to continue to your tailored advice."
        )
        return {"human_feedback": feedback if feedback and feedback.strip() else None}

    def route_by_verdict(state: HiringState) -> str:
        return state["fit_score"].verdict

    def prep_interview(state: HiringState):
        output = interview_prep_agent.run(
            llm, state["job_analysis"], state["fit_score"], state.get("human_feedback")
        )
        return {"output": output, "messages": [AIMessage(content=output)]}

    def analyze_gaps(state: HiringState):
        output = gap_analyzer_agent.run(
            llm, state["job_analysis"], state["fit_score"], state.get("human_feedback")
        )
        return {"output": output, "messages": [AIMessage(content=output)]}

    def advise_role(state: HiringState):
        output = role_advisor_agent.run(
            llm, state["job_analysis"], state["fit_score"], state.get("human_feedback")
        )
        return {"output": output, "messages": [AIMessage(content=output)]}

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
        messages = current.values.get("messages") or []
        if messages:
            print(messages[-1].content)
        for task in current.tasks:
            for i in task.interrupts:
                print(f"\n{i.value}")
        feedback = input("\n> ").strip()
        graph.invoke(Command(resume=feedback), config=config)

    return graph.get_state(config).values["output"]
