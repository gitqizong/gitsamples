"""Flask UI for semantic search demo."""

from __future__ import annotations

from flask import Flask, render_template, request

from semantic_search import build_index, search

app = Flask(__name__)

SAMPLE_ARTICLES = [
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
    {
        "id": 4,
        "title": "Embedding Stores",
        "body": "Vector stores keep embeddings for fast similarity search.",
    },
]

COLLECTION = build_index(SAMPLE_ARTICLES)


@app.route("/", methods=["GET", "POST"])
def index() -> str:
    query = ""
    hits: list[dict] = []
    if request.method == "POST":
        query = (request.form.get("query") or "").strip()
        if query:
            hits = search(COLLECTION, query, k=5)
    return render_template("index.html", query=query, hits=hits)


if __name__ == "__main__":
    app.run(debug=True)
