from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from src.graphs.chat.nodes import (
    agent_guardrails_agent,
    general_assistant_agent,
    intent_agent,
    order_management_agent,
    product_discovery_agent,
    user_guardrails_agent,
)
from src.graphs.chat.states import AgentState, Intent

_ROUTE_BY_INTENT = {
    Intent.ORDER_MANAGEMENT: "order_management",
    Intent.PRODUCT_DISCOVERY: "product_discovery",
    Intent.GENERAL: "general_assistant",
}


def route_user_guardrails(state: AgentState) -> str:
    return "end" if state.user_guardrail_flag else "intent"


def route_intent(state: AgentState) -> str:
    return _ROUTE_BY_INTENT.get(state.intent, "product_discovery")


def build_graph():
    """user_guardrails -> intent -> domain agent/general -> agent_guardrails -> END."""
    workflow = StateGraph(AgentState)
    workflow.add_node("user_guardrails_agent", user_guardrails_agent)
    workflow.add_node("intent_agent", intent_agent)
    workflow.add_node("order_management_agent", order_management_agent)
    workflow.add_node("product_discovery_agent", product_discovery_agent)
    workflow.add_node("general_assistant_agent", general_assistant_agent)
    workflow.add_node("agent_guardrails_agent", agent_guardrails_agent)
    workflow.set_entry_point("user_guardrails_agent")
    workflow.add_conditional_edges(
        "user_guardrails_agent",
        route_user_guardrails,
        {
            "intent": "intent_agent",
            "end": END,
        },
    )
    workflow.add_conditional_edges(
        "intent_agent",
        route_intent,
        {
            "order_management": "order_management_agent",
            "product_discovery": "product_discovery_agent",
            "general_assistant": "general_assistant_agent",
        },
    )
    workflow.add_edge("order_management_agent", "agent_guardrails_agent")
    workflow.add_edge("product_discovery_agent", "agent_guardrails_agent")
    workflow.add_edge("general_assistant_agent", "agent_guardrails_agent")
    workflow.add_edge("agent_guardrails_agent", END)
    checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer)
