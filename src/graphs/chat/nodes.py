import asyncio
import logging

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from src.config import settings
from src.embedding.openai import OpenAIEmbedding
from src.graphs.chat.prompts import (
    GUARDRAILS_GENERAL_PROMPT,
    INTENT_CLASSIFIER_PROMPT,
    ORDER_MANAGEMENT_SYSTEM_PROMPT,
    PRODUCT_DISCOVERY_SYSTEM_PROMPT,
)
from src.graphs.chat.states import AgentState, Intent
from src.llm.openai import OpenAILLM
from src.tools import order_management_tools, product_discovery_tools
from src.tools.mcp import get_mcp_tools
from src.tools.rag import create_rag_tools
from src.tools.search import get_web_search_tools
from src.vector_db.weaviate import WeaviateVectorDB

logger = logging.getLogger(__name__)
_llm = OpenAILLM()


def _order_management_tool_list():
    tools = list(order_management_tools)
    tools.extend(get_mcp_tools())
    try:
        db = WeaviateVectorDB(url=settings.WEAVIATE_URL)
        embedding = OpenAIEmbedding()
        tools.extend(
            create_rag_tools(
                vector_db=db,
                embedding=embedding,
            )
        )
    except Exception:
        pass
    return tools


_order_management_tools = _order_management_tool_list()
_order_management_react = create_agent(
    model=_llm.model,
    tools=_order_management_tools,
    system_prompt=ORDER_MANAGEMENT_SYSTEM_PROMPT,
)

_product_discovery_tools = list(product_discovery_tools) + get_web_search_tools()
_product_discovery_react = create_agent(
    model=_llm.model,
    tools=_product_discovery_tools,
    system_prompt=PRODUCT_DISCOVERY_SYSTEM_PROMPT,
)


def _messages_for_llm_no_tools(messages: list) -> list:
    out = []
    for m in messages:
        if isinstance(m, HumanMessage):
            out.append(m)
        elif isinstance(m, AIMessage) and (m.content or "").strip():
            out.append(AIMessage(content=m.content))
    return out


def intent_agent(state: AgentState) -> dict:
    if not state.messages:
        return {"intent": Intent.PRODUCT_DISCOVERY}
    messages_for_llm = [
        SystemMessage(content=INTENT_CLASSIFIER_PROMPT)
    ] + _messages_for_llm_no_tools(state.messages)
    response = _llm.model.invoke(messages_for_llm)
    raw = response.content or ""
    raw_upper = raw.upper().strip()
    if Intent.ORDER_MANAGEMENT.value in raw_upper:
        intent = Intent.ORDER_MANAGEMENT
    elif Intent.PRODUCT_DISCOVERY.value in raw_upper:
        intent = Intent.PRODUCT_DISCOVERY
    elif Intent.GENERAL.value in raw_upper:
        intent = Intent.GENERAL
    else:
        intent = Intent.PRODUCT_DISCOVERY
    logger.info("intent_agent classified intent=%s", intent.value)
    return {"intent": intent}


def _log_tools_and_reply(new_messages: list, node_name: str) -> None:
    tools_used = []
    last_content = ""
    for m in new_messages:
        if isinstance(m, ToolMessage):
            name = getattr(m, "name", None) or getattr(m, "tool_call_id", "?")
            tools_used.append(name)
        elif isinstance(m, AIMessage):
            last_content = (
                (m.content or "")
                if isinstance(m.content, str)
                else str(m.content or "")
            )
    if tools_used:
        logger.info("%s tools_used=%s", node_name, tools_used)
    if last_content:
        logger.info("%s reply (first 200)=%s", node_name, last_content[:200])


def order_management_agent(state: AgentState) -> dict:
    result = asyncio.run(_order_management_react.ainvoke({"messages": state.messages}))
    new_msgs = result["messages"][len(state.messages):]
    _log_tools_and_reply(new_msgs, "order_management_agent")
    return {"messages": new_msgs}


def product_discovery_agent(state: AgentState) -> dict:
    result = _product_discovery_react.invoke({"messages": state.messages})
    new_msgs = result["messages"][len(state.messages):]
    _log_tools_and_reply(new_msgs, "product_discovery_agent")
    return {"messages": new_msgs}


def general_assistant_agent(state: AgentState) -> dict:
    if state.intent == Intent.GENERAL:
        messages = [SystemMessage(content=GUARDRAILS_GENERAL_PROMPT)] + list(
            state.messages
        )
        response = _llm.model.invoke(messages)
        reply = (
            response.content
            or "I'm here to help. You can ask about orders, tracking, or browse our products."
        )
        return {"messages": [AIMessage(content=reply)]}
    return {}
