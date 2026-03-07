import uuid
from typing import Any
from urllib.parse import urlparse

import weaviate
from weaviate.classes.config import Configure, DataType, Property
from weaviate.classes.query import Filter, MetadataQuery

from src.vector_db.base import VectorDBBase


class WeaviateVectorDB(VectorDBBase):
    """
    Weaviate implementation of the VectorDBBase interface.

    This implementation uses Weaviate as the vector database backend.
    Embeddings are handled externally — no vectorizer module is configured
    in Weaviate itself. Pass pre-computed vectors via the `vectors` kwarg
    in add_documents, and via `query_vector` in semantic_search.

    Example:
        # Local instance
        db = WeaviateVectorDB(url="http://localhost:8090")

        # Cloud instance
        db = WeaviateVectorDB(
            url="https://your-cluster.weaviate.network",
            api_key="your-api-key"
        )
    """

    def __init__(
        self,
        url: str = "http://localhost:8090",
        api_key: str | None = None,
        collection_name: str = "Documents",
        **kwargs,
    ):
        """
        Initialize Weaviate vector database connection.

        Args:
            url: Weaviate instance URL (e.g. http://localhost:8090)
            api_key: Optional API key for Weaviate Cloud authentication
            collection_name: Default collection name to use
            **kwargs: Additional Weaviate client configuration
        """
        self.url = url
        self.api_key = api_key
        self.collection_name = collection_name

        if api_key:
            self.client = weaviate.connect_to_weaviate_cloud(
                cluster_url=url,
                auth_credentials=weaviate.auth.AuthApiKey(api_key),
                **kwargs,
            )
        else:
            parsed = urlparse(url)
            host = parsed.hostname or "localhost"
            port = parsed.port or 8090
            self.client = weaviate.connect_to_local(host=host, port=port, **kwargs)

        self._ensure_collection_exists()

    def _ensure_collection_exists(self):
        """Ensure the default collection exists."""
        if not self.client.collections.exists(self.collection_name):
            self.create_collection(self.collection_name)

    def add_documents(
        self,
        documents: list[str],
        metadatas: list[dict[str, Any]] | None = None,
        ids: list[str] | None = None,
        **kwargs,
    ) -> list[str]:
        """
        Add documents to Weaviate.

        Args:
            documents: List of text documents to add
            metadatas: Optional list of metadata dictionaries
            ids: Optional list of UUIDs (will be generated if not provided)
            **kwargs: Additional parameters. Pass `vectors` as a list of
                      pre-computed embedding vectors (List[List[float]]) when
                      embeddings are handled externally.

        Returns:
            List of document UUIDs that were added
        """
        collection = self.client.collections.get(self.collection_name)
        vectors: list[list[float]] | None = kwargs.get("vectors")

        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]

        if metadatas is None:
            metadatas = [{} for _ in documents]

        added_ids = []
        with collection.batch.dynamic() as batch:
            for i, (doc_id, document, metadata) in enumerate(
                zip(ids, documents, metadatas)
            ):
                properties = {"content": document, **metadata}
                vector = vectors[i] if vectors and i < len(vectors) else None
                batch.add_object(properties=properties, uuid=doc_id, vector=vector)
                added_ids.append(doc_id)

        return added_ids

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
            query: The search query text (unused when query_vector is provided)
            top_k: Number of results to return
            metadata_filter: Optional metadata filter
            **kwargs: Additional search parameters. Pass `query_vector` as a
                      pre-computed embedding vector (List[float]) when embeddings
                      are handled externally.

        Returns:
            List of search results with documents, scores, and metadata
        """
        collection = self.client.collections.get(self.collection_name)
        query_vector: list[float] | None = kwargs.get("query_vector")

        search_kwargs = {
            "limit": top_k,
            "return_metadata": MetadataQuery(distance=True),
        }

        if metadata_filter:
            search_kwargs["filters"] = self._build_filter(metadata_filter)

        if query_vector is not None:
            search_kwargs["near_vector"] = query_vector
            response = collection.query.near_vector(**search_kwargs)
        else:
            search_kwargs["query"] = query
            response = collection.query.near_text(**search_kwargs)

        results = []
        for obj in response.objects:
            result = {
                "id": str(obj.uuid),
                "document": obj.properties.get("content", ""),
                "score": 1 - obj.metadata.distance if obj.metadata.distance else 0,
                "metadata": {k: v for k, v in obj.properties.items() if k != "content"},
            }
            results.append(result)

        return results

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
            top_k: Number of results to return
            alpha: Weight between semantic (1.0) and keyword (0.0) search
            metadata_filter: Optional metadata filter
            **kwargs: Additional search parameters

        Returns:
            List of search results with documents, scores, and metadata
        """
        collection = self.client.collections.get(self.collection_name)
        query_vector: list[float] | None = kwargs.get("query_vector")

        search_kwargs: dict[str, Any] = {
            "query": query,
            "limit": top_k,
            "alpha": alpha,
            "return_metadata": MetadataQuery(score=True),
        }
        if query_vector is not None:
            search_kwargs["vector"] = query_vector
        if metadata_filter:
            search_kwargs["filters"] = self._build_filter(metadata_filter)

        response = collection.query.hybrid(**search_kwargs)

        results = []
        for obj in response.objects:
            result = {
                "id": str(obj.uuid),
                "document": obj.properties.get("content", ""),
                "score": obj.metadata.score if obj.metadata.score else 0,
                "metadata": {k: v for k, v in obj.properties.items() if k != "content"},
            }
            results.append(result)

        return results

    def delete_documents(
        self,
        ids: list[str] | None = None,
        metadata_filter: dict[str, Any] | None = None,
        **kwargs,
    ) -> bool:
        """
        Delete documents from Weaviate.

        Args:
            ids: Optional list of document UUIDs to delete
            metadata_filter: Optional metadata filter to select documents
            **kwargs: Additional parameters

        Returns:
            True if deletion was successful
        """
        collection = self.client.collections.get(self.collection_name)

        try:
            if ids:
                for doc_id in ids:
                    collection.data.delete_by_id(uuid=doc_id)
            elif metadata_filter:
                weaviate_filter = self._build_filter(metadata_filter)
                collection.data.delete_many(where=weaviate_filter)
            else:
                raise ValueError("Either ids or filter must be provided")

            return True
        except Exception as e:
            print(f"Error deleting documents: {e}")
            return False

    def update_documents(
        self,
        ids: list[str],
        documents: list[str] | None = None,
        metadatas: list[dict[str, Any]] | None = None,
        **kwargs,
    ) -> bool:
        """
        Update existing documents in Weaviate.

        Args:
            ids: List of document UUIDs to update
            documents: Optional list of new document texts
            metadatas: Optional list of new metadata dictionaries
            **kwargs: Additional parameters

        Returns:
            True if update was successful
        """
        collection = self.client.collections.get(self.collection_name)

        try:
            for i, doc_id in enumerate(ids):
                properties = {}

                if documents and i < len(documents):
                    properties["content"] = documents[i]

                if metadatas and i < len(metadatas):
                    properties.update(metadatas[i])

                if properties:
                    collection.data.update(uuid=doc_id, properties=properties)

            return True
        except Exception as e:
            print(f"Error updating documents: {e}")
            return False

    def get_documents(
        self,
        ids: list[str] | None = None,
        metadata_filter: dict[str, Any] | None = None,
        limit: int | None = None,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """
        Retrieve documents from Weaviate.

        Args:
            ids: Optional list of document UUIDs to retrieve
            metadata_filter: Optional metadata filter
            limit: Optional maximum number of documents
            **kwargs: Additional parameters

        Returns:
            List of documents with their metadata
        """
        collection = self.client.collections.get(self.collection_name)
        results = []

        try:
            if ids:
                for doc_id in ids:
                    obj = collection.query.fetch_object_by_id(uuid=doc_id)
                    if obj:
                        results.append(
                            {
                                "id": str(obj.uuid),
                                "document": obj.properties.get("content", ""),
                                "metadata": {
                                    k: v
                                    for k, v in obj.properties.items()
                                    if k != "content"
                                },
                            }
                        )
            else:
                query_kwargs = {}
                if metadata_filter:
                    query_kwargs["filters"] = self._build_filter(metadata_filter)
                if limit:
                    query_kwargs["limit"] = limit

                response = collection.query.fetch_objects(**query_kwargs)

                for obj in response.objects:
                    results.append(
                        {
                            "id": str(obj.uuid),
                            "document": obj.properties.get("content", ""),
                            "metadata": {
                                k: v
                                for k, v in obj.properties.items()
                                if k != "content"
                            },
                        }
                    )
        except Exception as e:
            print(f"Error retrieving documents: {e}")

        return results

    def create_collection(self, collection_name: str, **kwargs) -> bool:
        """
        Create a new collection in Weaviate.

        Args:
            collection_name: Name of the collection to create
            **kwargs: Additional configuration (vectorizer, properties, etc.)

        Returns:
            True if collection was created successfully
        """
        try:
            properties = kwargs.get(
                "properties", [Property(name="content", data_type=DataType.TEXT)]
            )

            self.client.collections.create(
                name=collection_name,
                vectorizer_config=Configure.Vectorizer.none(),
                properties=properties,
            )
            return True
        except Exception as e:
            print(f"Error creating collection: {e}")
            return False

    def delete_collection(self, collection_name: str, **kwargs) -> bool:
        """
        Delete a collection from Weaviate.

        Args:
            collection_name: Name of the collection to delete
            **kwargs: Additional parameters

        Returns:
            True if collection was deleted successfully
        """
        try:
            self.client.collections.delete(collection_name)
            return True
        except Exception as e:
            print(f"Error deleting collection: {e}")
            return False

    def list_collections(self, **kwargs) -> list[str]:
        """
        List all collections in Weaviate.

        Args:
            **kwargs: Additional parameters

        Returns:
            List of collection names
        """
        try:
            collections = self.client.collections.list_all()
            return [col.name for col in collections]
        except Exception as e:
            print(f"Error listing collections: {e}")
            return []

    def close(self) -> None:
        """Close the Weaviate client connection."""
        if self.client:
            self.client.close()

    def _build_filter(self, filter_dict: dict[str, Any]) -> Filter:
        """
        Build a Weaviate filter from a dictionary.

        Args:
            filter_dict: Dictionary with filter conditions

        Returns:
            Weaviate Filter object
        """
        filters = []
        for key, value in filter_dict.items():
            if isinstance(value, dict):
                operator = list(value.keys())[0]
                operand = value[operator]

                if operator == "$eq":
                    filters.append(Filter.by_property(key).equal(operand))
                elif operator == "$ne":
                    filters.append(Filter.by_property(key).not_equal(operand))
                elif operator == "$gt":
                    filters.append(Filter.by_property(key).greater_than(operand))
                elif operator == "$gte":
                    filters.append(Filter.by_property(key).greater_or_equal(operand))
                elif operator == "$lt":
                    filters.append(Filter.by_property(key).less_than(operand))
                elif operator == "$lte":
                    filters.append(Filter.by_property(key).less_or_equal(operand))
            else:
                filters.append(Filter.by_property(key).equal(value))

        if len(filters) == 1:
            return filters[0]
        elif len(filters) > 1:
            result = filters[0]
            for f in filters[1:]:
                result = result & f
            return result

        return None
