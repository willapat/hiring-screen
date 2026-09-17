from langchain_core.messages import HumanMessage, SystemMessage
from tools.ats_models import AtsReport

SYSTEM_PROMPT = """You are an ATS (applicant tracking system) consultant. You'll be given the
results of a deterministic scan of a candidate's resume PDF — a list of checks, each with a status
(pass/warn/fail/skip), a point weight, and a plain-English detail explaining what was found and why
it matters.

Turn this into a short, prioritized narrative for the candidate:

1. Lead with a one-sentence verdict referencing the actual score and grade.
2. List the warn/fail checks in order of weight (highest first) — for each, give the concrete fix
   in one or two sentences. Skip passing checks entirely; don't list them.
3. If there are no warn/fail checks, say so plainly and give one sentence of encouragement.
4. If keyword coverage against a job description is included, mention the missing keywords by name.

Only reference facts present in what you were given — do not invent findings, and don't repeat a
check's detail verbatim; rephrase it as actionable advice. Keep the whole thing under 250 words."""


def run(llm, report: AtsReport) -> str:
    check_lines = [
        f"- [{c.status.upper()}] weight={c.weight} {c.label}: {c.detail}"
        for c in report.checks
    ]
    human_message = (
        f"ATS Score: {report.score}/100 ({report.grade})\n"
        f"Reading order fidelity: {report.reading_order_fidelity:.0%}\n\n"
        f"Checks:\n" + "\n".join(check_lines)
    )

    if report.keyword_coverage:
        kc = report.keyword_coverage
        human_message += (
            f"\n\nKeyword coverage against the job description: {kc.pct}%\n"
            f"Covered: {', '.join(kc.covered) or 'none'}\n"
            f"Matched via alias/acronym: {', '.join(kc.alias_only) or 'none'}\n"
            f"Missing: {', '.join(kc.missing) or 'none'}"
        )

    result = llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=human_message)])

    content = result.content
    if isinstance(content, list):
        return "".join(b["text"] for b in content if b.get("type") == "text")
    return content
