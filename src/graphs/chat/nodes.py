import logging

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, ToolMessage
from src.config import settings
from src.embedding.openai import OpenAIEmbedding
from src.graphs.chat.prompts import SYSTEM_PROMPT
from src.graphs.chat.states import AgentState
from src.llm.openai import OpenAILLM
from src.tools import all_tools
from src.tools.rag import create_rag_tools
from src.tools.search import get_web_search_tools
from src.vector_db.weaviate import WeaviateVectorDB

logger = logging.getLogger(__name__)
_llm = OpenAILLM()


def _build_tool_list():
    tools = list(all_tools)
    try:
        db = WeaviateVectorDB(url=settings.WEAVIATE_URL)
        embedding = OpenAIEmbedding()
        tools.extend(create_rag_tools(vector_db=db, embedding=embedding))
    except Exception:
        pass
    tools.extend(get_web_search_tools())
    return tools


_all_tools = _build_tool_list()
_react = create_agent(
    model=_llm.model,
    tools=_all_tools,
    system_prompt=SYSTEM_PROMPT,
)


def assistant(state: AgentState) -> dict:
    result = _react.invoke({"messages": state.messages})
    new_msgs = result["messages"][len(state.messages):]
    # Log tool usage
    tools_used = [m.name for m in new_msgs if isinstance(m, ToolMessage)]
    if tools_used:
        logger.info("assistant tools_used=%s", tools_used)
    return {"messages": new_msgs}
