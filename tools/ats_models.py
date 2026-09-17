from typing import Literal
from pydantic import BaseModel, Field

CheckStage = Literal["extraction", "reading_order", "segmentation", "field_extraction", "skills", "advisory"]
CheckStatus = Literal["pass", "warn", "fail", "skip"]


class AtsCheck(BaseModel):
    id: str
    label: str
    stage: CheckStage
    status: CheckStatus
    weight: int = Field(ge=0, description="Points deducted from 100 on fail; half that on warn")
    detail: str
    evidence: list[str] = Field(default_factory=list)


class KeywordCoverage(BaseModel):
    covered: list[str]
    missing: list[str]
    alias_only: list[str] = Field(default_factory=list, description="Matched via an alias/acronym, not literally present")
    pct: float = Field(ge=0, le=100)


class AtsReport(BaseModel):
    score: int = Field(ge=0, le=100)
    grade: Literal["A", "B", "C", "D", "F"]
    reading_order_fidelity: float = Field(ge=0, le=1)
    checks: list[AtsCheck]
    keyword_coverage: KeywordCoverage | None = None
    narrative_markdown: str | None = None
    llm_used: bool = False
