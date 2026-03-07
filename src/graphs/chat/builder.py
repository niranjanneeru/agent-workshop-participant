from langgraph.graph import END, StateGraph
from src.graphs.chat.nodes import assistant
from src.graphs.chat.states import AgentState


def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("assistant", assistant)
    workflow.set_entry_point("assistant")
    workflow.add_edge("assistant", END)
    return workflow.compile()
