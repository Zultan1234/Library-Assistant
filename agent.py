"""MCP library agent. OpenAI Agents SDK, Gemini model."""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, Runner, set_tracing_disabled
from agents import OpenAIChatCompletionsModel
from agents.mcp import MCPServerStdio

ROOT = Path(__file__).resolve().parent
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
DEFAULT_MODEL = "gemini-3.5-flash-lite"


def build_agent(mcp_server):
    """Use the Agents SDK with Gemini's OpenAI-compatible endpoint."""
    load_dotenv(ROOT / ".env")
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing. Get a key from aistudio.google.com/apikey.")
    set_tracing_disabled(True)  # No OpenAI tracing or OpenAI API key needed.
    model_client = AsyncOpenAI(api_key=api_key, base_url=GEMINI_BASE_URL)
    model = OpenAIChatCompletionsModel(
        model=os.getenv("GEMINI_MODEL", DEFAULT_MODEL),
        openai_client=model_client,
    )
    return Agent(
        name="Library Assistant",
        model=model,
        instructions=(
            "You help students search and reserve books in a sample library. "
            "Use the MCP tools for every lookup or reservation. "
            "Call search_books for searches, reserve_book for a specified book ID, "
            "and find_and_reserve to search and reserve in one request. "
            "If a student name is missing for a reservation, ask for it. "
            "Never invent book details or claim a reservation succeeded if ok is false."
        ),
        mcp_servers=[mcp_server],
    )


async def run_prompts(prompts: list[str]):
    """Connect to a real stdio MCP server and run the given prompts."""
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
        for prompt in prompts:
            print("\nUSER:", prompt, flush=True)
            result = await Runner.run(agent, prompt)
            for item in result.new_items:
                if item.type == "tool_call_item":
                    name = getattr(item.raw_item, "name", "MCP tool")
                    print("  TOOL CALLED:", name)
                elif item.type == "tool_call_output_item":
                    print("  TOOL RESULT:", str(item.output)[:900])
            print("AGENT:", result.final_output, flush=True)


async def interactive():
    print("Campus Library | Gemini | enter 'exit' to finish")
    while True:
        try:
            prompt = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if prompt.lower() in {"exit", "quit"}:
            break
        if prompt:
            try:
                await run_prompts([prompt])
            except Exception as exc:
                print("Error:", exc)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", help="Run one request")
    args = parser.parse_args()
    if args.once:
        asyncio.run(run_prompts([args.once]))
    else:
        asyncio.run(interactive())
