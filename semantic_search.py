"""Simple semantic search using ChromaDB and sentence-transformers."""

from __future__ import annotations

from typing import Iterable

import chromadb
from chromadb.utils import embedding_functions


def build_index(articles: list[dict]) -> chromadb.Collection:
    """Build a Chroma collection from article dictionaries."""
    client = chromadb.Client()
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    collection = client.create_collection(
        name="articles",
        embedding_function=embedding_fn,
    )

    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict] = []

    for article in _normalize_articles(articles):
        ids.append(article["id"])
        documents.append(article["body"])
        metadatas.append({"title": article["title"]})

    if ids:
        collection.add(ids=ids, documents=documents, metadatas=metadatas)
    return collection


def search(collection: chromadb.Collection, query: str, k: int = 5) -> list[dict]:
    """Search the collection and return matching ids, titles, and scores."""
    results = collection.query(
        query_texts=[query],
        n_results=k,
        include=["distances", "metadatas"],
    )

    hits = []
    ids = results.get("ids", [[]])[0]
    distances = results.get("distances", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    for doc_id, distance, metadata in zip(ids, distances, metadatas):
        hits.append(
            {
                "id": doc_id,
                "title": metadata.get("title", ""),
                "score": distance,
            }
        )
    return hits


def _normalize_articles(articles: Iterable[dict]) -> list[dict]:
    normalized: list[dict] = []
    for article in articles:
        normalized.append(
            {
                "id": str(article["id"]),
                "title": str(article["title"]),
                "body": str(article["body"]),
            }
        )
    return normalized


if __name__ == "__main__":
    sample_articles = [
        {
            "id": 1,
            "title": "ChromaDB Overview",
            "body": "ChromaDB is a vector database for building AI applications.",
        },
        {
            "id": 2,
            "title": "Sentence Transformers",
            "body": "Sentence transformers create embeddings for semantic search.",
        },
        {
            "id": 3,
            "title": "Traditional Search",
            "body": "Keyword search matches exact terms in documents.",
        },
    ]

    collection = build_index(sample_articles)
    for hit in search(collection, "embedding database", k=3):
        print(f"{hit['id']}: {hit['title']} (score={hit['score']:.4f})")
