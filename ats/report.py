import sys

from ats.checks import CHECKS, compute_reading_order_fidelity
from ats.extract import ExtractedPdf, extract
from tools.ats_models import AtsReport, KeywordCoverage

GRADE_THRESHOLDS = [(90, "A"), (80, "B"), (70, "C"), (60, "D")]

ALIAS_GROUPS = [
    {"machine learning", "ml"},
    {"javascript", "js"},
    {"typescript", "ts"},
    {"kubernetes", "k8s"},
    {"amazon web services", "aws"},
    {"continuous integration", "ci"},
    {"continuous integration/continuous deployment", "ci/cd", "cicd"},
    {"natural language processing", "nlp"},
    {"artificial intelligence", "ai"},
    {"user interface", "ui"},
    {"user experience", "ux"},
    {"application programming interface", "api"},
    {"structured query language", "sql"},
    {"object-oriented programming", "oop"},
    {"continuous delivery", "cd"},
]


def _grade_for(score: int) -> str:
    for threshold, grade in GRADE_THRESHOLDS:
        if score >= threshold:
            return grade
    return "F"


def _alias_group_for(term_lower: str) -> set[str]:
    for group in ALIAS_GROUPS:
        if term_lower in group:
            return group
    return {term_lower}


def compute_keyword_coverage(resume_text: str, required_skills: list[str]) -> KeywordCoverage:
    text_lower = resume_text.lower()
    covered, missing, alias_only = [], [], []

    for skill in required_skills:
        skill_lower = skill.lower()
        if skill_lower in text_lower:
            covered.append(skill)
            continue
        aliases = _alias_group_for(skill_lower) - {skill_lower}
        if any(alias in text_lower for alias in aliases):
            alias_only.append(skill)
        else:
            missing.append(skill)

    total = len(required_skills)
    pct = round(100 * (len(covered) + len(alias_only)) / total, 1) if total else 100.0
    return KeywordCoverage(covered=covered, missing=missing, alias_only=alias_only, pct=pct)


def scan(pdf: ExtractedPdf, required_skills: list[str] | None = None) -> AtsReport:
    check_results = [fn(pdf) for fn in CHECKS]

    penalty = sum(c.weight for c in check_results if c.status == "fail")
    penalty += sum(c.weight * 0.5 for c in check_results if c.status == "warn")
    score = max(0, min(100, round(100 - penalty)))

    keyword_coverage = compute_keyword_coverage(pdf.text, required_skills) if required_skills else None

    return AtsReport(
        score=score,
        grade=_grade_for(score),
        reading_order_fidelity=compute_reading_order_fidelity(pdf),
        checks=check_results,
        keyword_coverage=keyword_coverage,
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m ats.report <path-to-resume.pdf>")
        sys.exit(1)

    report = scan(extract(sys.argv[1]))

    print(f"ATS Score: {report.score}/100 ({report.grade})")
    print(f"Reading order fidelity: {report.reading_order_fidelity:.0%}\n")

    marker = {"pass": "✓", "warn": "!", "fail": "✗", "skip": "-"}
    for c in report.checks:
        print(f"[{marker[c.status]}] ({c.weight:>2}) {c.label}: {c.detail}")
        for e in c.evidence:
            print(f"       - {e}")
