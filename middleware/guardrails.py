from pydantic import BaseModel
from langchain_core.messages import SystemMessage, HumanMessage


class GuardrailResult(BaseModel):
    is_valid: bool
    message: str


SYSTEM_PROMPT = """You are a content validator for a job application analysis tool.

Determine if the provided text is a legitimate job description or job posting.

A valid job description typically includes a role title, responsibilities, and required skills.
It does NOT need to be perfectly formatted — rough copy-pastes from job boards are fine.

Return is_valid=false only if the text is clearly not a job description (gibberish, random text, a question, code, etc.).
When in doubt, return is_valid=true.

If invalid, write a short helpful message telling the user what to provide."""


def check(llm, job_description: str) -> GuardrailResult:
    structured_llm = llm.with_structured_output(GuardrailResult)
    return structured_llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Is this a legitimate job description?\n\n{job_description}"),
    ])
