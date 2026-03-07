import logging

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, ToolMessage
from src.graphs.chat.prompts import SYSTEM_PROMPT
from src.graphs.chat.states import AgentState
from src.llm.openai import OpenAILLM
from src.tools import all_tools

logger = logging.getLogger(__name__)
_llm = OpenAILLM()

_react = create_agent(
    model=_llm.model,
    tools=all_tools,
    system_prompt=SYSTEM_PROMPT,
)


def assistant(state: AgentState) -> dict:
    result = _react.invoke({"messages": state.messages})
    new_msgs = result["messages"][len(state.messages):]
    # Log tool usage
    tools_used = [m.name for m in new_msgs if isinstance(m, ToolMessage)]
    if tools_used:
        logger.info("assistant tools_used=%s", tools_used)
    return {"messages": new_msgs}
