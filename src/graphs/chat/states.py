from enum import StrEnum
from typing import Annotated

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel


class Intent(StrEnum):
    ORDER_MANAGEMENT = "ORDER_MANAGEMENT"
    PRODUCT_DISCOVERY = "PRODUCT_DISCOVERY"
    GENERAL = "GENERAL"


class AgentState(BaseModel):
    messages: Annotated[list[AnyMessage], add_messages]
    intent: Intent | None = None
    user_guardrail_flag: bool = False
    agent_response_safe: bool = True
