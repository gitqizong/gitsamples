"""Index file names from a directory into ChromaDB and run semantic search."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions


def create_collection(persist_path: str, collection_name: str) -> chromadb.Collection:
    client = chromadb.PersistentClient(path=persist_path)
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    return client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_fn,
    )


def index_file_names(
    collection: chromadb.Collection,
    directory: str,
    recursive: bool,
    clear_first: bool,
) -> int:
    base = Path(directory).expanduser().resolve()
    if not base.exists() or not base.is_dir():
        raise ValueError(f"Directory does not exist: {base}")

    if clear_first:
        existing = collection.get(include=[])
        existing_ids = existing.get("ids", [])
        if existing_ids:
            collection.delete(ids=existing_ids)

    pattern = "**/*" if recursive else "*"
    files = [p for p in base.glob(pattern) if p.is_file()]

    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict] = []

    for file_path in files:
        rel_path = str(file_path.relative_to(base)).replace("\\", "/")
        content = (
            f"file name {file_path.name} path {rel_path} extension {file_path.suffix.lstrip('.')}"
        )
        item_id = hashlib.sha1(rel_path.encode("utf-8")).hexdigest()

        ids.append(item_id)
        documents.append(content)
        metadatas.append(
            {
                "file_name": file_path.name,
                "relative_path": rel_path,
                "extension": file_path.suffix.lstrip("."),
            }
        )

    if ids:
        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    return len(ids)


def search_file_names(
    collection: chromadb.Collection,
    query: str,
    limit: int,
) -> list[dict]:
    results = collection.query(
        query_texts=[query],
        n_results=limit,
        include=["distances", "metadatas"],
    )

    hits: list[dict] = []
    ids = results.get("ids", [[]])[0]
    distances = results.get("distances", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    for doc_id, distance, metadata in zip(ids, distances, metadatas):
        hits.append(
            {
                "id": doc_id,
                "score": distance,
                "file_name": metadata.get("file_name", ""),
                "relative_path": metadata.get("relative_path", ""),
                "extension": metadata.get("extension", ""),
            }
        )
    return hits


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Index directory file names into ChromaDB and search semantically."
    )
    parser.add_argument(
        "--persist-path",
        default=".chroma_file_names",
        help="Path for persistent ChromaDB data.",
    )
    parser.add_argument(
        "--collection",
        default="file_names",
        help="Chroma collection name.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    index_parser = subparsers.add_parser("index", help="Index file names from a directory.")
    index_parser.add_argument("--dir", required=True, help="Directory to scan.")
    index_parser.add_argument(
        "--recursive",
        action="store_true",
        help="Scan directories recursively.",
    )
    index_parser.add_argument(
        "--clear-first",
        action="store_true",
        help="Delete existing records in collection before indexing.",
    )

    search_parser = subparsers.add_parser("search", help="Search indexed file names.")
    search_parser.add_argument("--query", required=True, help="Semantic query text.")
    search_parser.add_argument("--limit", type=int, default=10, help="Max number of results.")

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    collection = create_collection(args.persist_path, args.collection)

    if args.command == "index":
        count = index_file_names(
            collection=collection,
            directory=args.dir,
            recursive=args.recursive,
            clear_first=args.clear_first,
        )
        print(f"Indexed {count} files into collection '{args.collection}'.")
        return

    hits = search_file_names(
        collection=collection,
        query=args.query,
        limit=args.limit,
    )
    if not hits:
        print("No matches found.")
        return

    for i, hit in enumerate(hits, start=1):
        print(
            f"{i}. {hit['relative_path']} "
            f"(file={hit['file_name']}, ext={hit['extension']}, score={hit['score']:.4f})"
        )


if __name__ == "__main__":
    main()

