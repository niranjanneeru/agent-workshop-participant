from langchain_core.messages import HumanMessage
from src.graphs.chat.builder import build_graph
from src.graphs.chat.states import AgentState


class ChatAgent:
    def __init__(self):
        self.graph = build_graph()

    def chat(self, message, thread_id, user_id, history=None):
        messages = [HumanMessage(content=message)]
        return self.graph.invoke(AgentState(messages=messages))
