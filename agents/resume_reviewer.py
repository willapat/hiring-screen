from pydantic import BaseModel
from langchain_core.messages import HumanMessage, SystemMessage
from tools.review_models import ReviewIssue

SYSTEM_PROMPT = """You are a resume editor. You'll be given a candidate's resume text with line
numbers prefixed to each line. Find concrete problems — weak or passive bullet phrasing, missing
quantification, vague impact, formatting inconsistencies, grammar issues — and return them as a
list of structured issues.

For each issue's "quote" field: copy the exact characters from the cited line, including any typos
or odd spacing — do not correct or paraphrase it. Also give the "line" number it came from. This is
critical: the quote must be copyable verbatim from that line, or the system cannot locate it in the
original document.

Categories: clarity, impact, formatting, grammar, quantification, tailoring, other.
Severities: low, medium, high — reserve high for things that would make a recruiter skip the resume.

Find the most impactful 5-12 issues. Don't nitpick minor stylistic preferences with no real impact."""


class _ReviewIssues(BaseModel):
    issues: list[ReviewIssue]


def run(llm, resume_text: str) -> list[ReviewIssue]:
    numbered_text = "\n".join(f"{i + 1:>4}| {line}" for i, line in enumerate(resume_text.splitlines()))
    structured_llm = llm.with_structured_output(_ReviewIssues)

    result = structured_llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Resume (line-numbered):\n\n{numbered_text}"),
    ])
    return result.issues
