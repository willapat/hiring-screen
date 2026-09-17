from functools import lru_cache
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool

_ddg = DuckDuckGoSearchRun(max_results=5)


@tool
@lru_cache(maxsize=128)
def search(query: str) -> str:
    """Search the web for current information (company info, market/role context, etc).
    Input should be a search query."""
    try:
        return _ddg.invoke(query)
    except Exception:
        return "Web search is temporarily unavailable — proceed using only what you already know."
