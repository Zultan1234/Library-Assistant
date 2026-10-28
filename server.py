"""The library's three MCP tools, served over stdio."""

import sys
from typing import Any

from fastmcp import FastMCP

from library import find_and_reserve_catalog_book, reserve_catalog_book, search_catalog


mcp = FastMCP("Campus Library")


def log_call(message: str) -> None:
    # stdout is reserved for MCP messages. Keep diagnostics on stderr.
    print(f"[MCP server] {message}", file=sys.stderr, flush=True)


@mcp.tool()
def search_books(query: str) -> dict[str, Any]:
    """Data tool. Search titles, authors and topics without changing the catalog.

    Args:
        query: A title, author, or topic, such as 'Python'.

    Returns:
        An 'ok' flag, count, and matching books with their availability;
        otherwise an 'error' string.
    """
    log_call(f"search_books(query={query!r})")
    return search_catalog(query)


@mcp.tool()
def reserve_book(book_id: str, student_name: str) -> dict[str, Any]:
    """Action tool. Reserve one available book in the local catalog.

    Args:
        book_id: Exact book ID from search results, for example 'B001'.
        student_name: Name to save with this reservation.

    Returns:
        'ok' and reservation details; or an 'error' if the book cannot
        be reserved. A successful call changes data/books.json.
    """
    log_call(f"reserve_book(book_id={book_id!r}, student_name={student_name!r})")
    return reserve_catalog_book(book_id, student_name)


@mcp.tool()
def find_and_reserve(query: str, student_name: str) -> dict[str, Any]:
    """Orchestration tool. Search books, then reserve the first available match.

    Args:
        query: Title, author, or topic to search.
        student_name: Name to save with the reservation.

    Returns:
        'ok', the search count, and reservation details; or an 'error'.
        This coordinates the same search and reservation operations used
        by the Data and Action tools.
    """
    log_call(f"find_and_reserve(query={query!r}, student_name={student_name!r})")
    return find_and_reserve_catalog_book(query, student_name)


if __name__ == "__main__":
    mcp.run(transport="stdio")
