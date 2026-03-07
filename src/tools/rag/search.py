from typing import Any

from langchain_core.tools import tool

from src.embedding.base import EmbeddingBase
from src.vector_db.base import VectorDBBase


def create_rag_tools(
    vector_db: VectorDBBase,
    embedding: EmbeddingBase,
) -> list:
    """
    Factory that returns RAG tools for searching ingested policy documents
    (and related internal docs). Use with the ingest script: put policy
    PDFs/text in data/, run scripts/ingest.py, then the agent can search them.

    Args:
        vector_db: Any VectorDBBase implementation (e.g. WeaviateVectorDB).
        embedding: Any EmbeddingBase implementation (e.g. OpenAIEmbedding).

    Returns:
        A list of LangChain @tool functions ready to bind to an LLM agent.
    """

    @tool
    def semantic_search(query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Search the ingested-document knowledge base (files from data/) using semantic similarity.

        Use for natural-language search over uploaded docs (e.g. policy text, FAQs).

        Args:
            query: Natural-language search query.
            top_k: Maximum number of results to return (default 5).
        """
        query_vector = embedding.embed_query(query)
        results = vector_db.semantic_search(
            query=query,
            top_k=top_k,
            query_vector=query_vector,
        )
        return results

    @tool
    def hybrid_search(
        query: str,
        top_k: int = 5,
        alpha: float = 0.5,
    ) -> list[dict[str, Any]]:
        """Search the ingested-document knowledge base (files from data/) with semantic + keyword.

        Use for natural-language search over uploaded docs when the query has specific terms.

        Args:
            query: Natural-language search query.
            top_k: Maximum number of results (default 5).
            alpha: Balance semantic (1.0) vs keyword (0.0); default 0.5.
        """
        query_vector = embedding.embed_query(query)
        results = vector_db.hybrid_search(
            query=query,
            top_k=top_k,
            alpha=alpha,
            query_vector=query_vector,
        )
        return results

    @tool
    def filtered_search(
        query: str,
        metadata_filter: dict[str, Any],
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Search the ingested-document knowledge base (files from data/) with metadata filters.

        Use when scoping by source or other metadata on ingested documents.

        Args:
            query: Natural-language search query.
            metadata_filter: Metadata filter (e.g. {"source": "return_policy.pdf"}).
            top_k: Maximum number of results (default 5).
        """
        query_vector = embedding.embed_query(query)
        results = vector_db.semantic_search(
            query=query,
            top_k=top_k,
            metadata_filter=metadata_filter,
            query_vector=query_vector,
        )
        return results

    @tool
    def get_document_by_id(document_id: str) -> dict[str, Any]:
        """Retrieve a policy document by ID (e.g. from a previous search).

        Args:
            document_id: The document/chunk ID returned by a search.
        """
        results = vector_db.get_documents(ids=[document_id])
        if not results:
            return {"error": f"No document found with id '{document_id}'."}
        return results[0]

    return [
        semantic_search,
        hybrid_search,
        filtered_search,
        get_document_by_id,
    ]
