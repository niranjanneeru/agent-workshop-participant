from langchain_core.messages import AIMessage


class ChatAgent:
    def __init__(self):
        pass

    def chat(self, message, thread_id, user_id, history=None):
        return {"messages": [AIMessage(content="Agent not implemented yet. Follow PLAN.md!")]}
