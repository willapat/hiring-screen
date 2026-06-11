from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from tools.search import search
from tools.scoring import JobAnalysis, FitScore

SYSTEM_PROMPT = """You are an interview coach helping a candidate prepare for a role they are well-qualified for.

Your output should have four sections:

1. COMPANY BRIEF
   Key things to know walking into the interview — what the company does, culture, tech stack, anything notable from recent news.

2. LIKELY INTERVIEW QUESTIONS
   - 4-5 technical questions based on the required skills and responsibilities
   - 3-4 behavioral questions based on the role's responsibilities
   Be specific to this role, not generic.

3. TALKING POINTS
   For each matched skill, give one concrete talking point — how to position it for this specific role and company.
   For any partial matches (e.g. has Azure, role needs AWS), flag it: what to say, how to frame the transferability.

4. THINGS TO RESEARCH BEFORE THE INTERVIEW
   2-3 specific things the candidate should look up on their own (recent company news, a specific product, a tech the role uses heavily).

Search for the company's interview process and common questions for this role type to make your prep specific."""


def run(llm, job: JobAnalysis, fit: FitScore, human_notes: str = None) -> str:
    agent = create_react_agent(llm, tools=[search], prompt=SYSTEM_PROMPT)

    partial_match_text = ""
    if fit.partial_matches:
        lines = [f"  - Has {m.candidate_has}, role needs {m.required}: {m.note}" for m in fit.partial_matches]
        partial_match_text = "\nPartial matches (adjacent skills):\n" + "\n".join(lines)

    correction_text = f"\n\nCandidate correction: {human_notes}" if human_notes else ""

    human_message = f"""Prepare this candidate for their interview.

Role: {job.role_title} at {job.company_name}
Company summary: {job.company_summary}
Required skills: {', '.join(job.required_skills)}
Responsibilities: {', '.join(job.responsibilities)}

Candidate's matched skills: {', '.join(fit.matched_skills)}{partial_match_text}

Fit score: {fit.score}/100 — {fit.reasoning}{correction_text}"""

    result = agent.invoke({
        "messages": [HumanMessage(content=human_message)]
    })

    content = result["messages"][-1].content
    if isinstance(content, list):
        return "".join(b["text"] for b in content if b.get("type") == "text")
    return content
