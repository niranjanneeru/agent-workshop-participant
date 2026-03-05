from abc import ABC, abstractmethod

from langchain_core.embeddings import Embeddings


class EmbeddingBase(ABC):
    """
    Abstract base class for embedding model implementations.

    Wraps a LangChain Embeddings instance and provides a consistent interface
    for generating embeddings across different providers.
    """

    @property
    @abstractmethod
    def model(self) -> Embeddings:
        """Return the underlying LangChain embeddings instance."""
        ...

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for a list of documents.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors
        """
        ...

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        """
        Generate an embedding for a single query string.

        Args:
            text: Query string to embed

        Returns:
            Embedding vector
        """
        ...

    @abstractmethod
    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Async generate embeddings for a list of documents.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors
        """
        return await self.model.aembed_documents(texts)

    @abstractmethod
    async def aembed_query(self, text: str) -> list[float]:
        """
        Async generate an embedding for a single query string.

        Args:
            text: Query string to embed

        Returns:
            Embedding vector
        """
        return await self.model.aembed_query(text)
