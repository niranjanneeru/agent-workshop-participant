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

    def _config(self, thread_id: str):
        return {"configurable": {"thread_id": thread_id}}

    def _messages_for_invoke(
        self,
        message: str,
        history: list[BaseMessage],
        thread_id: str,
        user_id: int,
    ) -> list[BaseMessage]:
        first_turn = not any(isinstance(m, HumanMessage) for m in history)
        if first_turn:
            return [
                SystemMessage(content=_USER_SYSTEM.format(user_id=user_id)),
                HumanMessage(content=message),
            ]
        return [HumanMessage(content=message)]

    def chat(
        self,
        message: str,
        thread_id: str,
        user_id: int,
        history: list[BaseMessage] | None = None,
    ) -> dict:
        messages = self._messages_for_invoke(message, history or [], thread_id, user_id)
        return self.graph.invoke(
            AgentState(messages=messages), config=self._config(thread_id)
        )

    async def achat(
        self,
        message: str,
        thread_id: str,
        user_id: int,
        history: list[BaseMessage] | None = None,
    ) -> dict:
        messages = self._messages_for_invoke(message, history or [], thread_id, user_id)
        return await self.graph.ainvoke(
            AgentState(messages=messages), config=self._config(thread_id)
        )

    def stream(
        self,
        message: str,
        thread_id: str,
        user_id: int,
        history: list[BaseMessage] | None = None,
        stream_mode=None,
    ):
        if stream_mode is None:
            stream_mode = ["messages", "updates"]
        messages = self._messages_for_invoke(message, history, thread_id, user_id)
        return self.graph.stream(
            AgentState(messages=messages),
            stream_mode=stream_mode,
            config=self._config(thread_id),
        )

    async def astream(
        self,
        message: str,
        thread_id: str,
        user_id: int,
        history: list[BaseMessage] | None = None,
        stream_mode=None,
    ):
        if stream_mode is None:
            stream_mode = ["messages", "updates"]
        messages = self._messages_for_invoke(message, history or [], thread_id, user_id)
        async for chunk in self.graph.astream(
            AgentState(messages=messages),
            stream_mode=stream_mode,
            config=self._config(thread_id),
        ):
            yield chunk
