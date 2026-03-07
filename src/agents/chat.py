from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from src.graphs.chat.builder import build_graph
from src.graphs.chat.states import AgentState

_USER_SYSTEM = (
    "The customer's user_id on KV Kart is {user_id}. "
    "Use this to look up their orders, cart, profile, etc. when needed."
)


class ChatAgent:
    def __init__(self):
        self.graph = build_graph()

    def chat(self, message, thread_id, user_id, history=None):
        messages = [
            SystemMessage(content=_USER_SYSTEM.format(user_id=user_id)),
            HumanMessage(content=message),
        ]
        return self.graph.invoke(AgentState(messages=messages))
