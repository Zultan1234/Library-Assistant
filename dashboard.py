"""Local browser dashboard for the existing Campus Library MCP project.

Run: python dashboard.py
Uses only Python's standard library plus the project's installed dependencies.
Place this file and dashboard.html beside agent.py, server.py, and library.py.
"""

from __future__ import annotations

import asyncio
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from library import read_catalog

ROOT = Path(__file__).resolve().parent
HISTORY: list[dict[str, str]] = []
CHAT_LOCK = threading.Lock()


def _tool_calls(items: list) -> list[dict[str, str]]:
    """Extract real MCP calls/results from the Agents SDK's run events."""
    calls: list[dict[str, str]] = []
    for item in items:
        if item.type == "tool_call_item":
            calls.append({"name": str(getattr(item.raw_item, "name", "MCP tool")), "result": ""})
        elif item.type == "tool_call_output_item":
            output = item.output
            if isinstance(output, (dict, list)):
                display = json.dumps(output, ensure_ascii=False)
            else:
                display = str(output)
            # MCP results can be verbose. Keep the payload manageable for the UI.
            if calls:
                next_unfilled = next((call for call in calls if not call["result"]), None)
                if next_unfilled is not None:
                    next_unfilled["result"] = display[:1800]
            else:
                calls.append({"name": "MCP tool", "result": display[:1800]})
    return calls


async def _chat(message: str) -> dict:
    # Imports are delayed so the catalog dashboard can load without an API key.
    from agents import Runner
    from agents.mcp import MCPServerStdio
    from agent import build_agent

    async with MCPServerStdio(
        name="Campus Library MCP",
        params={
            "command": sys.executable,
            "args": [str(ROOT / "server.py")],
            "cwd": str(ROOT),
        },
        cache_tools_list=True,
    ) as mcp_server:
        agent = build_agent(mcp_server)
        # Send a small conversation history so follow-up questions work.
        messages = HISTORY[-16:] + [{"role": "user", "content": message}]
        result = await Runner.run(agent, messages)

    reply = str(result.final_output or "(No response from the agent.)")
    HISTORY.extend([
        {"role": "user", "content": message},
        {"role": "assistant", "content": reply},
    ])
    return {"reply": reply, "calls": _tool_calls(result.new_items)}


class DashboardHandler(BaseHTTPRequestHandler):
    server_version = "LibraryDashboard/1.0"

    def _json(self, status: int, body: dict) -> None:
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        if path in {"/", "/dashboard.html"}:
            try:
                body = (ROOT / "dashboard.html").read_bytes()
            except OSError as exc:
                self._json(500, {"error": f"Could not open dashboard.html: {exc}"})
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif path == "/api/books":
            try:
                books = read_catalog()
            except ValueError as exc:
                self._json(500, {"error": str(exc)})
                return
            self._json(200, {"books": books})
        else:
            self._json(404, {"error": "Not found"})

    def do_POST(self) -> None:
        if urlsplit(self.path).path != "/api/chat":
            self._json(404, {"error": "Not found"})
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 32_768:
                self._json(400, {"error": "Message is missing or too large."})
                return
            data = json.loads(self.rfile.read(size))
            message = data.get("message", "")
            if not isinstance(message, str) or not message.strip():
                self._json(400, {"error": "Enter a message."})
                return
            with CHAT_LOCK:
                result = asyncio.run(_chat(message.strip()))
            self._json(200, result)
        except (ValueError, json.JSONDecodeError) as exc:
            self._json(400, {"error": str(exc)})
        except Exception as exc:
            # Keep the server running if the model or API is unavailable.
            print(f"[Dashboard] Chat error: {exc}", file=sys.stderr, flush=True)
            self._json(500, {"error": str(exc)})

    def log_message(self, format: str, *args: object) -> None:
        # Hide frequent background book-refresh requests from the terminal.
        if not self.path.startswith("/api/books"):
            super().log_message(format, *args)


def main() -> None:
    if not (ROOT / "agent.py").exists() or not (ROOT / "server.py").exists():
        sys.exit("Put dashboard.py and dashboard.html in the main project folder, beside agent.py and server.py.")
    if not (ROOT / "dashboard.html").exists():
        sys.exit("dashboard.html is missing. Put it beside dashboard.py.")

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    server = ThreadingHTTPServer(("127.0.0.1", port), DashboardHandler)
    server.daemon_threads = True
    print(f"\nLibrary dashboard: http://127.0.0.1:{port}\nPress Ctrl+C to stop.\n", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
