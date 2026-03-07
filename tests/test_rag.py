import pytest

from src.config import settings
from src.embedding.openai import OpenAIEmbedding
from src.tools.rag.search import create_rag_tools
from src.vector_db.weaviate import WeaviateVectorDB

RAG_COLLECTION = "TestRAG"


@pytest.fixture(scope="module")
def weaviate_db():
    db = WeaviateVectorDB(
        url=settings.WEAVIATE_URL,
        collection_name=RAG_COLLECTION,
    )
    yield db
    db.close()


@pytest.fixture(scope="module")
def embedding():
    return OpenAIEmbedding()


@pytest.fixture(scope="module")
def rag_tools(weaviate_db, embedding):
    return create_rag_tools(vector_db=weaviate_db, embedding=embedding)


@pytest.fixture(scope="module")
def rag_ingested_doc_id(weaviate_db, embedding):
    text = "Our return policy allows returns within 30 days for unused items."
    vectors = embedding.embed_documents([text])
    ids = weaviate_db.add_documents(documents=[text], vectors=vectors)
    return ids[0]


@pytest.mark.integration
def test_rag_semantic_search_returns_ingested_doc(rag_tools, rag_ingested_doc_id):
    semantic = next(t for t in rag_tools if t.name == "semantic_search")
    result = semantic.invoke({"query": "return policy", "top_k": 5})
    assert len(result) >= 1
    docs = [r["document"] for r in result]
    assert any("return policy" in d.lower() for d in docs)


@pytest.mark.integration
def test_rag_hybrid_search_returns_ingested_doc(rag_tools, rag_ingested_doc_id):
    hybrid = next(t for t in rag_tools if t.name == "hybrid_search")
    result = hybrid.invoke({"query": "returns within 30 days", "top_k": 5})
    assert len(result) >= 1
    docs = [r["document"] for r in result]
    assert any("30 days" in d for d in docs)


@pytest.mark.integration
def test_rag_get_document_by_id_returns_doc(rag_tools, rag_ingested_doc_id):
    get_doc = next(t for t in rag_tools if t.name == "get_document_by_id")
    result = get_doc.invoke({"document_id": rag_ingested_doc_id})
    assert "document" in result
    assert "return policy" in result["document"].lower()
