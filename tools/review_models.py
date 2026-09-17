from typing import Literal
from pydantic import BaseModel, Field

IssueCategory = Literal["clarity", "impact", "formatting", "grammar", "quantification", "tailoring", "other"]
IssueSeverity = Literal["low", "medium", "high"]


class SpanModel(BaseModel):
    start: int
    end: int


class ReviewIssue(BaseModel):
    id: str
    category: IssueCategory
    severity: IssueSeverity
    quote: str = Field(description="Text copied verbatim from the resume, exactly as it appears")
    line: int = Field(description="1-indexed line number in the resume text where the quote appears")
    problem: str = Field(description="What's wrong, in one sentence")
    suggestion: str = Field(description="A concrete rewrite or fix")
    span: SpanModel | None = Field(default=None, description="Resolved location in the resume text; null if unresolvable")


class Segment(BaseModel):
    text: str
    issue_ids: list[str] = Field(default_factory=list)


class ReviewReport(BaseModel):
    issues: list[ReviewIssue]
    segments: list[Segment] = Field(default_factory=list)
    anchor_rate: float = Field(ge=0, le=1)
    summary_markdown: str | None = None
