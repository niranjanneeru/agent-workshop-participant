from typing import Annotated

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel


class AgentState(BaseModel):
    messages: Annotated[list[AnyMessage], add_messages]
