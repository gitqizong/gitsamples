"""Flask UI for file-name semantic search backed by ChromaDB."""

from __future__ import annotations

from pathlib import Path

from flask import Flask, abort, render_template, request, send_file

from file_name_semantic_search import (
    create_collection,
    get_hit_by_id,
    index_file_names,
    search_file_names,
)

app = Flask(__name__)

DEFAULT_PERSIST_PATH = ".chroma_file_names"
DEFAULT_COLLECTION_NAME = "file_names"


@app.route("/", methods=["GET", "POST"])
def index() -> str:
    form_data = {
        "persist_path": DEFAULT_PERSIST_PATH,
        "collection_name": DEFAULT_COLLECTION_NAME,
        "directory": "",
        "recursive": True,
        "clear_first": False,
        "query": "",
        "limit": 10,
    }
    hits: list[dict] = []
    status = ""
    error = ""

    if request.method == "POST":
        form_data["persist_path"] = (
            request.form.get("persist_path", DEFAULT_PERSIST_PATH).strip()
            or DEFAULT_PERSIST_PATH
        )
        form_data["collection_name"] = (
            request.form.get("collection_name", DEFAULT_COLLECTION_NAME).strip()
            or DEFAULT_COLLECTION_NAME
        )
        form_data["directory"] = request.form.get("directory", "").strip()
        form_data["query"] = request.form.get("query", "").strip()
        form_data["recursive"] = request.form.get("recursive") == "on"
        form_data["clear_first"] = request.form.get("clear_first") == "on"

        raw_limit = (request.form.get("limit") or "10").strip()
        try:
            form_data["limit"] = max(1, min(100, int(raw_limit)))
        except ValueError:
            form_data["limit"] = 10

        action = request.form.get("action", "").strip()
        try:
            collection = create_collection(
                persist_path=form_data["persist_path"],
                collection_name=form_data["collection_name"],
            )
            if action == "index":
                if not form_data["directory"]:
                    raise ValueError("Directory is required for indexing.")
                indexed = index_file_names(
                    collection=collection,
                    directory=form_data["directory"],
                    recursive=form_data["recursive"],
                    clear_first=form_data["clear_first"],
                )
                status = f"Indexed {indexed} files into '{form_data['collection_name']}'."
            elif action == "search":
                if not form_data["query"]:
                    raise ValueError("Query is required for search.")
                hits = search_file_names(
                    collection=collection,
                    query=form_data["query"],
                    limit=form_data["limit"],
                )
                status = f"Found {len(hits)} result(s)."
            else:
                error = "Unknown action."
        except Exception as exc:  # noqa: BLE001
            error = str(exc)

    return render_template(
        "file_name_search.html",
        form_data=form_data,
        hits=hits,
        status=status,
        error=error,
    )


@app.route("/open/<doc_id>", methods=["GET"])
def open_file(doc_id: str):
    persist_path = (request.args.get("persist_path") or DEFAULT_PERSIST_PATH).strip()
    collection_name = (request.args.get("collection_name") or DEFAULT_COLLECTION_NAME).strip()
    collection = create_collection(
        persist_path=persist_path,
        collection_name=collection_name,
    )
    hit = get_hit_by_id(collection, doc_id)
    if not hit:
        abort(404, description="Indexed file not found.")

    absolute_path = str(hit.get("absolute_path", "")).strip()
    file_path = Path(absolute_path)
    if not absolute_path or not file_path.exists() or not file_path.is_file():
        abort(404, description="File path no longer exists.")

    return send_file(file_path, as_attachment=False)


if __name__ == "__main__":
    app.run(debug=True)
