from typing import Any, AsyncIterator, Iterator

from langchain_core.messages import AIMessage, BaseMessage
from langchain_openai import ChatOpenAI

from src.config import settings
from src.llm.base import LLMBase


class OpenAILLM(LLMBase):
    """
    OpenAI implementation of LLMBase using langchain_openai.

    Example:
        llm = OpenAILLM()
        response = llm.invoke([HumanMessage(content="Hello!")])

        # Custom model/temperature
        llm = OpenAILLM(model="gpt-4o", temperature=0.7)
    """

    def __init__(
        self,
        model: str | None = None,
        temperature: float = 0.0,
        api_key: str | None = None,
        **kwargs,
    ):
        """
        Initialize the OpenAI LLM.

        Args:
            model: Model name (defaults to settings.OPENAI_LLM_MODEL)
            temperature: Sampling temperature
            api_key: OpenAI API key (defaults to settings.OPENAI_API_KEY)
            **kwargs: Additional parameters passed to ChatOpenAI
        """
        self._model = ChatOpenAI(
            model=model or settings.OPENAI_LLM_MODEL,
            temperature=temperature,
            api_key=api_key or settings.OPENAI_API_KEY or None,
            base_url=settings.LITELLM_URL,
            **kwargs,
        )

    @property
    def model(self) -> ChatOpenAI:
        return self._model

    def invoke(self, messages: list[BaseMessage], **kwargs) -> AIMessage:
        return self._model.invoke(messages, **kwargs)

    def stream(self, messages: list[BaseMessage], **kwargs) -> Iterator[Any]:
        return self._model.stream(messages, **kwargs)

    async def ainvoke(self, messages: list[BaseMessage], **kwargs) -> AIMessage:
        return await self._model.ainvoke(messages, **kwargs)

    async def astream(self, messages: list[BaseMessage], **kwargs) -> AsyncIterator[Any]:
        async for chunk in self._model.astream(messages, **kwargs):
            yield chunk
