from langchain_core.messages import SystemMessage, HumanMessage
from tools.scoring import JobAnalysis, FitScore

SYSTEM_PROMPT = """You are a technical recruiter evaluating how well a candidate's resume matches a job.

Scoring rules:
- Base your score only on required_skills — nice-to-have skills should not hurt the score if missing
- If the candidate has a closely related or transferable technology (e.g. Azure when AWS is required, Vue when React is required), put it in partial_matches — do not count it as fully missing
- Partial matches should contribute roughly half the weight of a full match when calculating the score

Verdict thresholds:
- strong  (75–100): has most required skills, partial matches cover any gaps well
- moderate (45–74): solid foundation but meaningful gaps, or heavy reliance on partials
- weak    (0–44):  missing most required skills with little transferable overlap

Be honest. Do not inflate scores."""


def run(llm, job: JobAnalysis, resume_text: str) -> FitScore:
    structured_llm = llm.with_structured_output(FitScore)

    human_message = f"""Job Details:
Role: {job.role_title} at {job.company_name}
Required skills: {', '.join(job.required_skills)}
Nice to have: {', '.join(job.nice_to_have)}
Responsibilities: {', '.join(job.responsibilities)}

Resume:
{resume_text}

Score this candidate's fit for the role."""

    return structured_llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=human_message),
    ])
