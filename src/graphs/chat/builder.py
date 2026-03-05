from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from src.graphs.chat.nodes import (
    general_assistant_agent, intent_agent,
    order_management_agent, product_discovery_agent,
)
from src.graphs.chat.states import AgentState, Intent

_ROUTE_BY_INTENT = {
    Intent.ORDER_MANAGEMENT: "order_management",
    Intent.PRODUCT_DISCOVERY: "product_discovery",
    Intent.GENERAL: "general_assistant",
}


def route_intent(state: AgentState) -> str:
    return _ROUTE_BY_INTENT.get(state.intent, "product_discovery")


def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("intent_agent", intent_agent)
    workflow.add_node("order_management_agent", order_management_agent)
    workflow.add_node("product_discovery_agent", product_discovery_agent)
    workflow.add_node("general_assistant_agent", general_assistant_agent)
    workflow.set_entry_point("intent_agent")
    workflow.add_conditional_edges("intent_agent", route_intent, {
        "order_management": "order_management_agent",
        "product_discovery": "product_discovery_agent",
        "general_assistant": "general_assistant_agent",
    })
    workflow.add_edge("order_management_agent", END)
    workflow.add_edge("product_discovery_agent", END)
    workflow.add_edge("general_assistant_agent", END)
    checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer)
