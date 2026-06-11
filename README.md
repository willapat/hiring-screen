# Hiring Screen

A multi-agent job-fit analyzer built on [LangGraph](https://langchain-ai.github.io/langgraph/). Give it a job description and your resume, and it scores how well you match, then routes you to tailored advice based on the strength of the fit.

## How it works

The pipeline is a LangGraph `StateGraph`. Each step is a node; routing between them is driven by the analysis itself.

```
input → validate → analyze job → score fit → human review → ┬→ strong  → interview prep
                                                             ├→ moderate → gap analysis
                                                             └→ weak     → role advice
```

1. **Validate** — a guardrail check confirms the input is actually a job description.
2. **Analyze job** — a ReAct agent extracts role, skills, and responsibilities, and searches the web for company context.
3. **Score fit** — the resume is scored against the required skills (0–100), with credit for adjacent/transferable skills (e.g. Azure when AWS is required).
4. **Human review** — the graph pauses (`interrupt`) so you can correct the score before it commits to a path.
5. **Route by verdict** — `strong` / `moderate` / `weak` each go to a different specialist agent:
   - **Strong** → interview prep (likely questions, talking points, company brief)
   - **Moderate** → gap analysis (what's missing, learning paths, projected score)
   - **Weak** → role advice (why it's a mismatch, better-fit roles)

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # then fill in your keys
```

You'll need a `GOOGLE_API_KEY` (for the Gemini model). The LangSmith keys are optional — they enable tracing.

## Usage

**CLI:**

```bash
python main.py
```

It asks for your resume path (`.pdf` or `.txt`), then for the job description (copy it to your clipboard and press Enter).

**LangGraph Studio:**

```bash
langgraph dev
```

Opens the graph in Studio for visual inspection and step-through debugging. The chat is a two-step conversation:

1. Paste the **job description** as your message and send.
2. Send your **resume** — either the **file path** to it (e.g. `/Users/you/resume.pdf`, read off disk since the dev server is local) or the **resume text** pasted directly.

It then scores your fit, pauses for review (send an empty message to accept, or type a correction), and posts your tailored advice in the chat.

> Note: Studio's chat file-attachment button does **not** deliver files to a custom-state graph like this one — use the file path instead.

## Visualizing the graph

```bash
python visualize.py
```

Prints a Mermaid diagram of the graph structure.

## Project layout

```
agents/
  supervisor.py     # builds the StateGraph, defines state and routing
  job_analyzer.py   # extracts job details + company research
  fit_scorer.py     # scores resume vs. required skills
  interview_prep.py # strong-fit path
  gap_analyzer.py   # moderate-fit path
  role_advisor.py   # weak-fit path
middleware/
  guardrails.py     # input validation
tools/
  scoring.py        # Pydantic schemas for structured output
  file_tools.py     # resume reading (PDF/TXT)
  search.py         # DuckDuckGo search tool
main.py             # CLI entry point
graph.py            # graph export for LangGraph Studio
```

## Stack

- **LangGraph** — `StateGraph`, `create_react_agent`, `interrupt` for human-in-the-loop
- **Gemini** (`gemini-3.1-flash-lite`) via `init_chat_model`
- **Pydantic** for structured LLM output
- **DuckDuckGo** for company/role research
