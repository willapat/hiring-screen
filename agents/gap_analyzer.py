from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from tools.search import search
from tools.scoring import JobAnalysis, FitScore

SYSTEM_PROMPT = """You are a career coach helping a candidate understand and close the gaps between their current skills and a job they almost qualify for.

Start with a short **WHERE YOU STAND** opener (2-3 sentences) before anything else: tell the candidate plainly that they're a moderate/partial match — close, but not quite there yet — what that means for applying now versus after some prep, and the highest-impact gap to focus on. Reference their actual score and reasoning. Be honest but encouraging.

Then give four sections:

1. GAP BREAKDOWN
   For each missing skill, explain why it matters specifically for this role — not just that it's missing, but what they'd actually use it for day-to-day.

2. QUICK WINS (partial matches first)
   Look at adjacent/transferable skills the candidate already has. For each one, explain what the bridge looks like — how long, what specifically to learn. These are the highest-ROI improvements.

3. LEARNING PATHS
   For each missing skill with no adjacent equivalent, give a concrete learning path: what to study, in what order, and a realistic timeline. Search for current resources.

4. PROJECTED SCORE
   Estimate what their fit score would be if they addressed the top 2-3 gaps. Be specific: "Closing the Kubernetes and AWS gaps would likely put you at ~78 (strong fit)." Explain the reasoning.

Be honest about effort. Don't sugarcoat a 6-month gap as a weekend project."""


def run(llm, job: JobAnalysis, fit: FitScore, human_notes: str = None) -> str:
    agent = create_react_agent(llm, tools=[search], prompt=SYSTEM_PROMPT)

    partial_match_text = ""
    if fit.partial_matches:
        lines = [f"  - Has {m.candidate_has}, role needs {m.required}: {m.note}" for m in fit.partial_matches]
        partial_match_text = "\nPartial matches (adjacent skills):\n" + "\n".join(lines)

    missing_text = ""
    if fit.missing_skills:
        missing_text = "\nMissing skills: " + ", ".join(fit.missing_skills)

    correction_text = f"\n\nCandidate correction: {human_notes}" if human_notes else ""

    human_message = f"""Analyze this candidate's gaps for the role and give them a plan to close them.

Role: {job.role_title} at {job.company_name}
Required skills: {', '.join(job.required_skills)}
Responsibilities: {', '.join(job.responsibilities)}

Candidate's matched skills: {', '.join(fit.matched_skills)}{partial_match_text}{missing_text}

Current fit score: {fit.score}/100 — {fit.reasoning}{correction_text}"""

    result = agent.invoke({
        "messages": [HumanMessage(content=human_message)]
    })

    content = result["messages"][-1].content
    if isinstance(content, list):
        return "".join(b["text"] for b in content if b.get("type") == "text")
    return content
