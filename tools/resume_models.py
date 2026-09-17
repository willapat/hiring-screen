from pydantic import BaseModel, Field


class ContactInfo(BaseModel):
    name: str
    email: str = ""
    phone: str = ""
    location: str = ""
    links: list[str] = Field(default_factory=list, description="Full URLs, e.g. LinkedIn, GitHub, portfolio")


class Entry(BaseModel):
    title: str = Field(description="e.g. job title, degree, or project name")
    subtitle: str = Field(default="", description="e.g. company or school name")
    location: str = ""
    date_range: str = ""
    bullets: list[str] = Field(default_factory=list)


class Section(BaseModel):
    heading: str = Field(description="e.g. Experience, Education, Skills, Projects")
    entries: list[Entry] = Field(default_factory=list)
    raw_text: str = Field(
        default="",
        description="For a flat single-line section like Skills, instead of structured entries. "
        "Keep it to one line — it renders as continuous flowing text, not separate paragraphs.",
    )


class StructuredResume(BaseModel):
    contact: ContactInfo
    summary: str = Field(default="", description="Optional professional summary/objective, 1-3 sentences")
    sections: list[Section] = Field(default_factory=list)
