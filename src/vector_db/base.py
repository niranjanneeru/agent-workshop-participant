from abc import ABC, abstractmethod
from typing import Any


class VectorDBBase(ABC):
    """
    Abstract base class for vector database implementations.

    This class provides a common interface for different vector database backends
    (e.g., Pinecone, Weaviate, Qdrant, ChromaDB, etc.). Extend this class to
    implement your preferred vector database solution.
    """

    @abstractmethod
    def __init__(self, **kwargs):
        """
        Initialize the vector database connection.

        Args:
            **kwargs: Database-specific configuration parameters
        """
        ...

    @abstractmethod
    def add_documents(
        self,
        documents: list[str],
        metadatas: list[dict[str, Any]] | None = None,
        ids: list[str] | None = None,
        **kwargs,
    ) -> list[str]:
        """
        Add documents to the vector database.

        Args:
            documents: List of text documents to add
            metadatas: Optional list of metadata dictionaries for each document
            ids: Optional list of unique identifiers for each document
            **kwargs: Additional database-specific parameters

        Returns:
            List of document IDs that were added
        """
        ...

    @abstractmethod
    def semantic_search(
        self,
        query: str,
        top_k: int = 5,
        metadata_filter: dict[str, Any] | None = None,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """
        Perform semantic search using vector similarity.

        Args:
            query: The search query text
            top_k: Number of top results to return
            metadata_filter: Optional metadata filter to apply
            **kwargs: Additional database-specific parameters

        Returns:
            List of search results with documents, scores, and metadata
        """
        ...

    @abstractmethod
    def hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        alpha: float = 0.5,
        metadata_filter: dict[str, Any] | None = None,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """
        Perform hybrid search combining semantic and keyword search.

        Args:
            query: The search query text
            top_k: Number of top results to return
            alpha: Weight between semantic (1.0) and keyword (0.0) search
            metadata_filter: Optional metadata filter to apply
            **kwargs: Additional database-specific parameters

        Returns:
            List of search results with documents, scores, and metadata
        """
        ...

    @abstractmethod
    def delete_documents(
        self,
        ids: list[str] | None = None,
        metadata_filter: dict[str, Any] | None = None,
        **kwargs,
    ) -> bool:
        """
        Delete documents from the vector database.

        Args:
            ids: Optional list of document IDs to delete
            metadata_filter: Optional metadata filter to select documents to delete
            **kwargs: Additional database-specific parameters

        Returns:
            True if deletion was successful
        """
        ...

    @abstractmethod
    def update_documents(
        self,
        ids: list[str],
        documents: list[str] | None = None,
        metadatas: list[dict[str, Any]] | None = None,
        **kwargs,
    ) -> bool:
        """
        Update existing documents in the vector database.

        Args:
            ids: List of document IDs to update
            documents: Optional list of new document texts
            metadatas: Optional list of new metadata dictionaries
            **kwargs: Additional database-specific parameters

        Returns:
            True if update was successful
        """
        ...

    @abstractmethod
    def get_documents(
        self,
        ids: list[str] | None = None,
        metadata_filter: dict[str, Any] | None = None,
        limit: int | None = None,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """
        Retrieve documents from the vector database.

        Args:
            ids: Optional list of document IDs to retrieve
            metadata_filter: Optional metadata filter to apply
            limit: Optional maximum number of documents to return
            **kwargs: Additional database-specific parameters

        Returns:
            List of documents with their metadata
        """
        ...

    @abstractmethod
    def create_collection(self, collection_name: str, **kwargs) -> bool:
        """
        Create a new collection/index in the vector database.

        Args:
            collection_name: Name of the collection to create
            **kwargs: Additional database-specific parameters (e.g., dimension, distance metric)

        Returns:
            True if collection was created successfully
        """
        ...

    @abstractmethod
    def delete_collection(self, collection_name: str, **kwargs) -> bool:
        """
        Delete a collection/index from the vector database.

        Args:
            collection_name: Name of the collection to delete
            **kwargs: Additional database-specific parameters

        Returns:
            True if collection was deleted successfully
        """
        ...

    @abstractmethod
    def list_collections(self, **kwargs) -> list[str]:
        """
        List all collections/indexes in the vector database.

        Args:
            **kwargs: Additional database-specific parameters

        Returns:
            List of collection names
        """
        ...

    def close(self) -> None:
        """
        Close the database connection and cleanup resources.

        Override this method if your implementation requires cleanup.
        """
        ...

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
