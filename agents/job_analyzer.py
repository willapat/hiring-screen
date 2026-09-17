from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from tools.search import search
from tools.scoring import JobAnalysis

SYSTEM_PROMPT = """You are a job description analyst.

Given a job posting, your job is to:
1. Extract the role title, company name, required skills, nice-to-have skills, and key responsibilities directly from the posting
2. Search for context about the company — look up things like "[company name] engineering culture", "[company name] tech stack", "[company name] about"
3. Use your search results to write a short company summary

Be thorough with required vs nice-to-have skills — only mark something as required if the posting explicitly says so."""


def run(llm, job_description: str) -> JobAnalysis:
    agent = create_react_agent(
        llm,
        tools=[search],
        prompt=SYSTEM_PROMPT,
        response_format=JobAnalysis,
    )

    result = agent.invoke(
        {"messages": [HumanMessage(content=f"Analyze this job posting:\n\n{job_description}")]},
        config={"recursion_limit": 8},
    )

    return result["structured_response"]
