from pydantic import BaseModel
from langchain_core.messages import HumanMessage, SystemMessage
from tools.review_models import ReviewIssue
from tools.scoring import FitScore, JobAnalysis

SYSTEM_PROMPT = """You are a resume tailoring assistant. You'll be given a candidate's resume text
with line numbers prefixed to each line, plus the job they're applying for and how they scored
against it.

Suggest specific, concrete rewrites that would make this resume fit THIS job better — reword a
bullet to foreground a matched skill, work in a missing keyword the candidate genuinely has
evidence for elsewhere in the resume, reorder emphasis, etc. Every suggestion must be grounded in
something already true about the candidate — never invent experience they don't have.

For each suggestion's "quote" field: copy the exact characters from the cited line, including any
typos or odd spacing — do not correct or paraphrase it. Also give the "line" number it came from.
This is critical: the quote must be copyable verbatim from that line, or the system cannot locate
it in the original document.

Use category "tailoring" for all of these. Severities: low, medium, high — reserve high for gaps
that would make the difference between an interview and a rejection.

Give the 3-8 highest-impact tailoring suggestions. Focus on the missing_skills and partial_matches
first — those are the biggest opportunities."""


class _TailoringIssues(BaseModel):
    issues: list[ReviewIssue]


def run(llm, resume_text: str, job: JobAnalysis, fit: FitScore) -> list[ReviewIssue]:
    numbered_text = "\n".join(f"{i + 1:>4}| {line}" for i, line in enumerate(resume_text.splitlines()))
    structured_llm = llm.with_structured_output(_TailoringIssues)

    partial_text = ""
    if fit.partial_matches:
        lines = [f"  - Has {m.candidate_has}, role needs {m.required}: {m.note}" for m in fit.partial_matches]
        partial_text = "\nPartial matches (adjacent skills):\n" + "\n".join(lines)

    human_message = f"""Role: {job.role_title} at {job.company_name}
Required skills: {', '.join(job.required_skills)}
Responsibilities: {', '.join(job.responsibilities)}

Current fit: {fit.score}/100 ({fit.verdict})
Matched skills: {', '.join(fit.matched_skills)}{partial_text}
Missing skills: {', '.join(fit.missing_skills)}

Resume (line-numbered):

{numbered_text}"""

    result = structured_llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=human_message),
    ])
    return result.issues
