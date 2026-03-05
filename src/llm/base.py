from abc import ABC, abstractmethod
from typing import Any, Iterator

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage


class LLMBase(ABC):
    """
    Abstract base class for LLM implementations.

    Wraps a LangChain BaseChatModel and provides a consistent interface
    for invoking language models across different providers.
    """

    @property
    @abstractmethod
    def model(self) -> BaseChatModel:
        """Return the underlying LangChain chat model instance."""
        ...

    @abstractmethod
    def invoke(self, messages: list[BaseMessage], **kwargs) -> AIMessage:
        """
        Invoke the LLM with a list of messages.

        Args:
            messages: List of LangChain messages (HumanMessage, SystemMessage, etc.)
            **kwargs: Additional provider-specific parameters

        Returns:
            AIMessage with the model response
        """
        ...

    @abstractmethod
    def stream(self, messages: list[BaseMessage], **kwargs) -> Iterator[Any]:
        """
        Stream the LLM response.

        Args:
            messages: List of LangChain messages
            **kwargs: Additional provider-specific parameters

        Yields:
            Streamed response chunks
        """
        ...

    @abstractmethod
    async def ainvoke(self, messages: list[BaseMessage], **kwargs) -> AIMessage:
        """
        Async invoke the LLM.

        Args:
            messages: List of LangChain messages
            **kwargs: Additional provider-specific parameters

        Returns:
            AIMessage with the model response
        """
        return await self.model.ainvoke(messages, **kwargs)

    @abstractmethod
    async def astream(self, messages: list[BaseMessage], **kwargs):
        """
        Async stream the LLM response.

        Args:
            messages: List of LangChain messages
            **kwargs: Additional provider-specific parameters

        Yields:
            Streamed response chunks
        """
        async for chunk in self.model.astream(messages, **kwargs):
            yield chunk
