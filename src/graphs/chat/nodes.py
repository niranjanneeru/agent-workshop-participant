import asyncio
import logging

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from pydantic import BaseModel

from src.config import settings
from src.embedding.openai import OpenAIEmbedding
from src.graphs.chat.prompts import (
    AGENT_GUARDRAILS_PROMPT,
    GUARDRAILS_GENERAL_PROMPT,
    INTENT_CLASSIFIER_PROMPT,
    ORDER_MANAGEMENT_SYSTEM_PROMPT,
    PRODUCT_DISCOVERY_SYSTEM_PROMPT,
    USER_GUARDRAILS_PROMPT,
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


class GuardrailResult(BaseModel):
    content: str
    flag: bool


_user_guardrails_llm = _llm.model.with_structured_output(GuardrailResult)
_agent_guardrails_llm = _llm.model.with_structured_output(GuardrailResult)


def _last_human_and_context(state: AgentState) -> list:
    history = list(state.messages)
    last_human_index = None
    for index in range(len(history) - 1, -1, -1):
        if isinstance(history[index], HumanMessage):
            last_human_index = index
            break

    if last_human_index is None:
        raw = history[-10:]
    else:
        start = max(0, last_human_index - 10)
        raw = history[start : last_human_index + 1]
    return _messages_for_llm_no_tools(raw)


def _last_ai_message_index(messages: list) -> int | None:
    for index in range(len(messages) - 1, -1, -1):
        if isinstance(messages[index], AIMessage):
            return index
    return None


def user_guardrails_agent(state: AgentState) -> dict:
    context_messages = _last_human_and_context(state)
    messages = [SystemMessage(content=USER_GUARDRAILS_PROMPT)] + context_messages
    result = _user_guardrails_llm.invoke(messages)
    if result.flag:
        blocked = (
            result.content.strip() or "I can only help with KVKart-related requests."
        )
        last_user = next(
            (
                m.content
                for m in reversed(state.messages)
                if isinstance(m, HumanMessage)
            ),
            "",
        )
        logger.warning(
            "user_guardrails_agent BLOCKED request | user_message=%s | response=%s",
            (last_user or "")[:200],
            blocked[:200],
        )
        return {
            "user_guardrail_flag": True,
            "messages": [AIMessage(content=blocked)],
        }
    return {"user_guardrail_flag": False}


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
    new_msgs = result["messages"][len(state.messages) :]
    _log_tools_and_reply(new_msgs, "order_management_agent")
    return {"messages": new_msgs}


def product_discovery_agent(state: AgentState) -> dict:
    result = _product_discovery_react.invoke({"messages": state.messages})
    new_msgs = result["messages"][len(state.messages) :]
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


def agent_guardrails_agent(state: AgentState) -> dict:
    messages = list(state.messages)
    ai_index = _last_ai_message_index(messages)
    if ai_index is None:
        return {
            "agent_response_safe": False,
            "messages": [AIMessage(content="Something went wrong")],
        }

    candidate = messages[ai_index].content or ""
    context = messages[max(0, ai_index - 10) : ai_index]
    context_for_llm = _messages_for_llm_no_tools(context)
    guardrail_messages = [
        SystemMessage(content=AGENT_GUARDRAILS_PROMPT),
        *context_for_llm,
        HumanMessage(content=f"Draft response to validate:\n{candidate}"),
    ]
    result = _agent_guardrails_llm.invoke(guardrail_messages)

    if result.flag:
        logger.warning(
            "agent_guardrails_agent FLAGGED draft (replaced with fallback) | draft_snippet=%s",
            candidate[:200],
        )
        return {
            "agent_response_safe": False,
            "messages": [AIMessage(content="Something went wrong")],
        }

    sanitized_content = result.content.strip()
    if not sanitized_content or sanitized_content == candidate:
        return {"agent_response_safe": True}

    if sanitized_content != candidate:
        logger.info("agent_guardrails_agent PII-masked response (content changed)")
    return {
        "agent_response_safe": True,
        "messages": [AIMessage(content=sanitized_content)],
    }
