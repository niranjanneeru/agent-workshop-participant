from langchain_tavily import TavilySearch

from src.config import settings


def get_web_search_tools() -> list:
    return [
        TavilySearch(
            tavily_api_key=settings.TAVILY_API_KEY,
            max_results=5,
            topic="general",
        ),
    ]
