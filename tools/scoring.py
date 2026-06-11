from typing import Literal
from pydantic import BaseModel, Field


class JobAnalysis(BaseModel):
    role_title: str
    company_name: str
    required_skills: list[str] = Field(description="Skills explicitly required in the job posting")
    nice_to_have: list[str] = Field(description="Skills listed as preferred or nice to have")
    responsibilities: list[str] = Field(description="Key responsibilities from the job posting")
    company_summary: str = Field(description="2-3 sentence summary of the company based on research")


class SkillMatch(BaseModel):
    required: str
    candidate_has: str
    note: str = Field(description="Why these are considered adjacent or transferable")


class FitScore(BaseModel):
    verdict: Literal["strong", "moderate", "weak"]
    score: int = Field(ge=0, le=100)
    matched_skills: list[str] = Field(description="Skills the candidate has that directly match the job")
    partial_matches: list[SkillMatch] = Field(description="Skills where candidate has an adjacent or transferable equivalent")
    missing_skills: list[str] = Field(description="Required skills the candidate has nothing close to")
    reasoning: str = Field(description="2-3 sentence explanation of the verdict and score")
