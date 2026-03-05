import pytest

from src.tools.search import get_web_search_tools


@pytest.fixture(scope="module")
def web_search_tools():
    return get_web_search_tools()


@pytest.mark.integration
def test_web_search_returns_results(web_search_tools):
    assert len(web_search_tools) >= 1
    tool = web_search_tools[0]
    result = tool.invoke({"query": "Python programming language"})
    assert result is not None
    if isinstance(result, list):
        assert len(result) >= 1
    else:
        assert len(str(result).strip()) >= 1
