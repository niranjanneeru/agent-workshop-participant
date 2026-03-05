from langchain_core.messages import SystemMessage
from src.graphs.chat.prompts import SYSTEM_PROMPT
from src.graphs.chat.states import AgentState
from src.llm.openai import OpenAILLM

_llm = OpenAILLM()


def assistant(state: AgentState) -> dict:
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(state.messages)
    response = _llm.model.invoke(messages)
    return {"messages": [response]}
