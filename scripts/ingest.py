"""
Ingest policy documents (and related internal docs) for the RAG knowledge base.

Loads .txt, .md, .pdf from data/, chunks them, embeds via OpenAIEmbedding,
and stores in Weaviate. Runs automatically when you docker compose up.
"""

import argparse
import sys
import uuid
from pathlib import Path

import pypdf

from src.config import settings
from src.embedding.openai import OpenAIEmbedding
from src.vector_db.weaviate import WeaviateVectorDB

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}


def load_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_pdf_file(path: Path) -> str:
    try:
        reader = pypdf.PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except ImportError:
        print(
            f"  [warn] pypdf not installed — skipping {path.name}. "
            "Install with: uv add pypdf"
        )
        return ""


def load_document(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".pdf":
        return load_pdf_file(path)
    return load_text_file(path)


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 100,
) -> list[str]:
    """Split text into overlapping chunks by character count."""
    if not text.strip():
        return []

    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == text_len:
            break
        start += chunk_size - chunk_overlap

    return chunks


def collect_documents(data_dir: Path) -> list[tuple[Path, str]]:
    """Return list of (path, text) for all supported files in data_dir."""
    docs = []
    for path in sorted(data_dir.iterdir()):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            print(f"  Loading: {path.name}")
            text = load_document(path)
            if text.strip():
                docs.append((path, text))
            else:
                print(f"  [warn] {path.name} is empty or unreadable — skipping.")
    return docs


def ingest(
    collection_name: str = "Documents",
    chunk_size: int = 1000,
    chunk_overlap: int = 100,
) -> None:
    if not DATA_DIR.exists():
        print(f"Data directory not found: {DATA_DIR}")
        sys.exit(1)

    print("\n=== Document Ingestion ===")
    print(f"Data dir   : {DATA_DIR}")
    print(f"Weaviate   : {settings.WEAVIATE_URL}")
    print(f"Collection : {collection_name}")
    print(f"Chunk size : {chunk_size} chars  |  Overlap: {chunk_overlap} chars")
    print()

    print("Step 1/4 — Collecting documents...")
    raw_docs = collect_documents(DATA_DIR)
    if not raw_docs:
        print("No supported documents found in data/. Add .txt, .md, or .pdf files.")
        sys.exit(0)
    print(f"  Found {len(raw_docs)} document(s).")

    print("\nStep 2/4 — Chunking documents...")
    all_chunks: list[str] = []
    all_metadatas: list[dict] = []
    all_ids: list[str] = []

    for path, text in raw_docs:
        chunks = chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        print(f"  {path.name}: {len(chunks)} chunk(s)")
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_metadatas.append(
                {
                    "source": path.name,
                    "chunk_index": i,
                }
            )
            all_ids.append(str(uuid.uuid4()))

    print(f"  Total chunks: {len(all_chunks)}")

    print("\nStep 3/4 — Embedding chunks via OpenAI...")
    embedder = OpenAIEmbedding(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.LITELLM_URL,
    )
    vectors = embedder.embed_documents(all_chunks)
    print(f"  Embedded {len(vectors)} chunk(s), dimension={len(vectors[0])}.")

    print("\nStep 4/4 — Ingesting into Weaviate...")
    db = WeaviateVectorDB(url=settings.WEAVIATE_URL, collection_name=collection_name)

    added_ids = db.add_documents(
        documents=all_chunks,
        metadatas=all_metadatas,
        ids=all_ids,
        vectors=vectors,
    )

    db.close()

    print(f"  Ingested {len(added_ids)} chunk(s) into collection '{collection_name}'.")
    print("\nDone!")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest documents into Weaviate for RAG."
    )
    parser.add_argument(
        "--collection",
        default="Documents",
        help="Weaviate collection name (default: Documents)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=500,
        help="Chunk size in characters (default: 1000)",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=50,
        help="Overlap between chunks in characters (default: 100)",
    )
    args = parser.parse_args()

    ingest(
        collection_name=args.collection,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )


if __name__ == "__main__":
    main()
