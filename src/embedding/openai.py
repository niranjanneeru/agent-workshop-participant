from langchain_openai import OpenAIEmbeddings

from src.config import settings
from src.embedding.base import EmbeddingBase


class OpenAIEmbedding(EmbeddingBase):
    """
    OpenAI implementation of EmbeddingBase using langchain_openai.

    Example:
        embedding = OpenAIEmbedding()
        vectors = embedding.embed_documents(["Hello world", "Foo bar"])
        query_vec = embedding.embed_query("Hello")

        # Custom model
        embedding = OpenAIEmbedding(model="text-embedding-3-large")
    """

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        **kwargs,
    ):
        """
        Initialize the OpenAI embedding model.

        Args:
            model: Model name (defaults to settings.OPENAI_EMBEDDING_MODEL)
            api_key: OpenAI API key (defaults to settings.OPENAI_API_KEY)
            base_url: API base URL (defaults to settings.LITELLM_URL so embeddings use the same proxy as chat)
            **kwargs: Additional parameters passed to OpenAIEmbeddings
        """
        self._model = OpenAIEmbeddings(
            model=model or settings.OPENAI_EMBEDDING_MODEL,
            api_key=api_key or settings.OPENAI_API_KEY or None,
            openai_api_base=base_url or settings.LITELLM_URL,
            **kwargs,
        )

    @property
    def model(self) -> OpenAIEmbeddings:
        return self._model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._model.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._model.embed_query(text)

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        return await self._model.aembed_documents(texts)

    async def aembed_query(self, text: str) -> list[float]:
        return await self._model.aembed_query(text)
