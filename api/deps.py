import json
from functools import lru_cache
from pathlib import Path

from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import MemorySaver

from api.config import get_settings
from api.store import LatexBuildStore, ResumeStore
from graphs.job_match import build_job_match_graph
from graphs.latex_export import build_latex_export_graph

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class _MockStructuredLLM:
    def __init__(self, model_cls):
        self._model_cls = model_cls

    def invoke(self, messages):
        fixture_path = FIXTURES_DIR / f"{self._model_cls.__name__}.json"
        if not fixture_path.exists():
            raise RuntimeError(
                f"MOCK_LLM=1 but no fixture found for {self._model_cls.__name__} "
                f"(expected {fixture_path})."
            )
        return self._model_cls.model_validate(json.loads(fixture_path.read_text()))


class MockLLM:
    """Stands in for a real chat model when MOCK_LLM=1, so the frontend can be
    built and exercised without spending real API quota. Covers the two call
    patterns the ATS/review agents use — plain .invoke() and
    .with_structured_output(Model).invoke() — by reading canned responses from
    api/fixtures/. It does not support tool calling, so it can't stand in for
    the react-agent-based job-match flow."""

    def invoke(self, messages, **kwargs):
        fixture_path = FIXTURES_DIR / "narrative.md"
        content = fixture_path.read_text() if fixture_path.exists() else "Mock LLM response."
        return AIMessage(content=content)

    def with_structured_output(self, model_cls, **kwargs):
        return _MockStructuredLLM(model_cls)


@lru_cache
def get_llm():
    settings = get_settings()
    if settings.mock_llm:
        return MockLLM()
    return init_chat_model(settings.model_name, model_provider="google_genai", temperature=0)


@lru_cache
def get_store() -> ResumeStore:
    return ResumeStore()


@lru_cache
def get_job_match_graph():
    """A single compiled graph shared across requests, with an in-memory
    checkpointer keyed by thread_id (== session_id). Requires running uvicorn
    with a single worker — MemorySaver is process-local, not shared."""
    return build_job_match_graph(get_llm(), checkpointer=MemorySaver(), pause_for_review=True)


@lru_cache
def get_latex_graph():
    return build_latex_export_graph(get_llm())


@lru_cache
def get_latex_store() -> LatexBuildStore:
    return LatexBuildStore()
