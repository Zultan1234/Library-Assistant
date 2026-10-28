"""Book catalog operations. No MCP or model code lives in this module."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_CATALOG = PROJECT_DIR / "data" / "books.json"


def catalog_path() -> Path:
    """Use a separate dataset in tests when BOOKS_FILE is set."""
    configured = os.getenv("BOOKS_FILE", "").strip()
    return Path(configured).expanduser() if configured else DEFAULT_CATALOG


def read_catalog() -> list[dict[str, Any]]:
    """Read and check the catalog before using it."""
    path = catalog_path()
    try:
        with path.open("r", encoding="utf-8") as handle:
            records = json.load(handle)
    except FileNotFoundError as exc:
        raise ValueError(f"Catalog not found: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read catalog: {exc}") from exc

    if not isinstance(records, list):
        raise ValueError("Catalog must contain a list of books.")
    for record in records:
        if (
            not isinstance(record, dict)
            or not all(k in record for k in ("id", "title", "author", "topics", "available", "reserved_for"))
            or not isinstance(record["available"], bool)
            or not isinstance(record["topics"], list)
        ):
            raise ValueError("Catalog has an invalid book entry.")
    return records


def write_catalog(records: list[dict[str, Any]]) -> None:
    """Save changes using a temporary file to avoid partial JSON writes."""
    path = catalog_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=".books-", suffix=".tmp", delete=False,
        ) as handle:
            temp_name = handle.name
            json.dump(records, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temp_name, path)
    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)


def search_catalog(query: str) -> dict[str, Any]:
    """Look up book titles, authors or topics; never change catalog data."""
    if not isinstance(query, str) or not query.strip():
        return {"ok": False, "error": "Enter a book title, author, or topic to search."}
    try:
        records = read_catalog()
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}

    terms = query.casefold().split()
    matches = []
    for book in records:
        searchable = " ".join(
            [str(book["title"]), str(book["author"]), *map(str, book["topics"])]
        ).casefold()
        if all(term in searchable for term in terms):
            matches.append({
                "id": book["id"],
                "title": book["title"],
                "author": book["author"],
                "available": book["available"],
            })

    return {"ok": True, "query": query.strip(), "count": len(matches), "matches": matches}


def reserve_catalog_book(book_id: str, student_name: str) -> dict[str, Any]:
    """Reserve one book and persist the change to the local JSON catalog."""
    if not isinstance(book_id, str) or not book_id.strip():
        return {"ok": False, "error": "Provide a book ID."}
    if not isinstance(student_name, str) or not student_name.strip():
        return {"ok": False, "error": "Provide a name for the reservation."}
    try:
        records = read_catalog()
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}

    normalized_id = book_id.strip().upper()
    for book in records:
        if str(book["id"]).upper() != normalized_id:
            continue
        if not book["available"]:
            return {"ok": False, "error": f"Book {book['id']} is already reserved."}
        book["available"] = False
        book["reserved_for"] = student_name.strip()
        try:
            write_catalog(records)
        except OSError as exc:
            return {"ok": False, "error": f"Could not save reservation: {exc}"}
        return {
            "ok": True,
            "book_id": book["id"],
            "title": book["title"],
            "reserved_for": book["reserved_for"],
            "message": "Reservation saved.",
        }
    return {"ok": False, "error": f"Book {normalized_id} was not found."}


def find_and_reserve_catalog_book(query: str, student_name: str) -> dict[str, Any]:
    """Use the read operation, then the write operation, for one request."""
    if not isinstance(student_name, str) or not student_name.strip():
        return {"ok": False, "error": "Provide a name for the reservation."}

    search_result = search_catalog(query)
    if not search_result["ok"]:
        return search_result
    if not search_result["matches"]:
        return {"ok": False, "error": f"No books matched '{query.strip()}'."}

    first_available = next(
        (book for book in search_result["matches"] if book["available"]), None
    )
    if first_available is None:
        return {"ok": False, "error": f"All books matching '{query.strip()}' are reserved."}

    reservation = reserve_catalog_book(first_available["id"], student_name)
    if not reservation["ok"]:
        return reservation
    return {
        "ok": True,
        "searched_for": query.strip(),
        "matches_found": search_result["count"],
        "reservation": reservation,
    }
