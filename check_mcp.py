"""Call the real MCP tools without an OpenAI API key.

This runs the FastMCP server in-process through an MCP client. It uses a
separate temporary copy of the catalog, so it won't change data/books.json.
"""

import asyncio
import json
import os
import shutil
import tempfile
from pathlib import Path

from fastmcp import Client
from server import mcp


ROOT = Path(__file__).resolve().parent


def unpack(result):
    """Get a dictionary from a FastMCP tool result."""
    if result.is_error:
        raise RuntimeError(f"MCP error: {result.content}")
    data = getattr(result, "data", None)
    if isinstance(data, dict):
        return data
    structured = getattr(result, "structured_content", None)
    if isinstance(structured, dict):
        return structured
    for block in result.content:
        if hasattr(block, "text"):
            return json.loads(block.text)
    raise RuntimeError("No JSON result returned by MCP server")


async def run_demo() -> None:
    with tempfile.TemporaryDirectory() as temp:
        demo_path = Path(temp) / "books.json"
        shutil.copyfile(ROOT / "data" / "books_original.json", demo_path)
        old_path = os.environ.get("BOOKS_FILE")
        os.environ["BOOKS_FILE"] = str(demo_path)
        try:
            async with Client(mcp) as client:
                tools = await client.list_tools()
                names = sorted(tool.name for tool in tools)
                expected = sorted(("search_books", "reserve_book", "find_and_reserve"))
                assert names == expected, f"Expected exactly 3 tools, got: {names}"
                print("Discovered tools:", ", ".join(names))

                calls = [
                    ("search_books", {"query": "Python"}),
                    ("reserve_book", {"book_id": "B001", "student_name": "Demo Student"}),
                    ("reserve_book", {"book_id": "B001", "student_name": "Demo Student"}),
                    ("find_and_reserve", {"query": "algorithms", "student_name": "Demo Student"}),
                    ("find_and_reserve", {"query": "not-a-real-topic", "student_name": "Demo Student"}),
                ]
                for name, arguments in calls:
                    response = unpack(await client.call_tool(name, arguments))
                    print(f"\n{name}({arguments}):")
                    print(json.dumps(response, indent=2))
                print("\nMCP checks finished. The original catalog was not modified.")
        finally:
            if old_path is None:
                os.environ.pop("BOOKS_FILE", None)
            else:
                os.environ["BOOKS_FILE"] = old_path


if __name__ == "__main__":
    asyncio.run(run_demo())
