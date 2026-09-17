from langchain_core.messages import HumanMessage, SystemMessage
from tools.resume_models import StructuredResume

SYSTEM_PROMPT = """You are a resume parser. Convert the given resume text into the structured
schema exactly — do not invent, embellish, or drop any content, and do not fix typos in the
person's actual work (that's a different tool's job).

Guidelines:
- contact.links should be the bare URLs as they appear (e.g. "linkedin.com/in/x", not markdown).
- Group naturally into sections using standard headings (Education, Experience, Projects, Skills,
  Leadership, etc.) based on what's already in the resume — don't invent new section types.
- Use `entries` for anything with a title/subtitle/dates/bullets shape (jobs, degrees, projects).
- Use `raw_text` instead of `entries` only for a flat section like Skills — keep it to one line of
  comma-separated content, since it renders as continuous flowing text.
- Preserve bullet text content faithfully; you may lightly clean up obvious PDF extraction
  artifacts (e.g. a spurious space inserted mid-word like "T echnology") but do not rewrite,
  summarize, or improve the writing itself."""


def run(llm, resume_text: str) -> StructuredResume:
    structured_llm = llm.with_structured_output(StructuredResume)
    return structured_llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Resume text:\n\n{resume_text}"),
    ])
