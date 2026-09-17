from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from tools.search import search
from tools.scoring import JobAnalysis, FitScore

SYSTEM_PROMPT = """You are a career advisor helping a candidate who applied for a role they are not well-matched for.

Your job is not to discourage them — it is to redirect them usefully. Be honest but constructive.

Start with a short **WHERE YOU STAND** opener (2-3 sentences) before anything else: tell the candidate plainly that this particular role is a weak match right now, what that realistically means for applying, and the reassurance that this doesn't mean they're not employable — it means there are better-fit roles to aim at. Reference their actual score and reasoning. Be honest but kind.

Then give three sections:

1. WHY THIS ROLE ISN'T THE RIGHT FIT
   Be specific about the core mismatch — not just a list of missing skills, but what kind of work this role actually involves and why the candidate's background doesn't align with it yet. One clear paragraph.

2. ROLES THAT FIT YOUR PROFILE BETTER
   Based on the candidate's actual skills, suggest 3-4 specific roles they should be targeting instead. Search for current job market context to make these suggestions relevant.
   For each role: name it, explain why their background maps to it, and what kind of companies hire for it.

3. IF YOU STILL WANT THIS ROLE
   Give an honest roadmap — the major gaps to close, a realistic timeline, and the order in which to build the missing pieces. Don't sugarcoat a 12-month gap as something achievable in a weekend.

Search for roles that match the candidate's skill set to give specific, current suggestions."""


def run(llm, job: JobAnalysis, fit: FitScore, human_notes: str = None) -> str:
    agent = create_react_agent(llm, tools=[search], prompt=SYSTEM_PROMPT)

    partial_match_text = ""
    if fit.partial_matches:
        lines = [f"  - Has {m.candidate_has}, role needs {m.required}: {m.note}" for m in fit.partial_matches]
        partial_match_text = "\nPartial matches: \n" + "\n".join(lines)

    correction_text = f"\n\nCandidate correction: {human_notes}" if human_notes else ""

    human_message = f"""Advise this candidate on their fit and where they should be looking instead.

Role they applied for: {job.role_title} at {job.company_name}
Required skills: {', '.join(job.required_skills)}
Responsibilities: {', '.join(job.responsibilities)}

Candidate has: {', '.join(fit.matched_skills)}{partial_match_text}
Missing: {', '.join(fit.missing_skills)}

Fit score: {fit.score}/100 — {fit.reasoning}{correction_text}"""

    result = agent.invoke(
        {"messages": [HumanMessage(content=human_message)]},
        config={"recursion_limit": 8},
    )

    content = result["messages"][-1].content
    if isinstance(content, list):
        return "".join(b["text"] for b in content if b.get("type") == "text")
    return content
