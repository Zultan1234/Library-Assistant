# Campus Library MCP (Gemini + Colab)

This project has exactly three MCP tools: `search_books` (Data), `reserve_book` (Action), and `find_and_reserve` (Orchestration). The server uses FastMCP; the agent uses the **OpenAI Agents SDK** with a **Gemini** model. The catalog is a local JSON file, not a real campus system.

Here is the youtube link to the demo:
https://youtu.be/700VUxdTTMc

## Recommended: Google Colab with dashboard

1. Extract this ZIP on your computer. Open https://colab.research.google.com/ and upload `C5_MCP_Dashboard_Colab.ipynb` from the extracted folder.
2. Select **Runtime > Run all**. When asked to upload a project ZIP, select `C5_Library_MCP_Complete.zip` (the ZIP you downloaded). Colab installs the packages on Google's runtime.
3. Enter your Gemini API key when prompted (https://aistudio.google.com/apikey).
4. Click **Open Library Dashboard** to view the chatbot, current book availability, reservations, and real MCP tool calls. If the preview cannot open, use the embedded dashboard in the next notebook cell.
5. The notebook also runs tests. To reset reservations or run the terminal agent instead, set `RESET_BOOKS` or `RUN_TERMINAL_AGENT` to `True` in the optional cell and run it.

The dashboard runs on Colab's hosted runtime, not as a local server on your computer. A Colab session can end, so download your updated catalog if you need to keep changes. Google's API free tier is subject to limits and availability. An OpenAI API key is not needed. Never include your real Gemini key in submissions.

The older `C5_Library_MCP_Gemini_Colab.ipynb` is retained unchanged for the terminal-only Colab workflow.

## Local dashboard (no additional dependencies)

After installing `requirements.txt` as described below, copy `.env.example` to `.env` and enter your Gemini API key. From the project folder run:

```bash
python dashboard.py
```

Open http://127.0.0.1:8000 in your browser. The page shows book status, reservations, a chatbot, and MCP tool calls. It uses the existing agent, FastMCP server, and Python standard library HTTP server; you do not need extra packages. Run `python reset_books.py` to restore all books to their original available state before recording a demo, then refresh the page.

## Local run (optional)

From the project folder, with Python 3.11+:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python check_mcp.py
```

Copy `.env.example` to `.env`, put your Gemini key there, then run `python agent.py`. Or use `python agent.py --once "Search for Python books"`. **Never submit `.env`**.

## Files

- `server.py`: exactly three MCP tools exposed over stdio.
- `dashboard.py` and `dashboard.html`: local web chat, live book availability/reservations, and MCP activity panel.
- `C5_MCP_Dashboard_Colab.ipynb`: upload this notebook to Colab, then upload this project ZIP to launch the dashboard on Colab.
- `C5_Library_MCP_Gemini_Colab.ipynb`: original terminal-oriented Colab notebook (kept for reference).
- `library.py`: JSON catalog search and reservation operations.
- `agent.py`: Gemini-backed OpenAI Agents SDK agent.
- `check_mcp.py`: MCP tool discovery and sample calls, no key required.
- `tests/test_library.py`: unit tests, including invalid input and duplicate reservation.
- `reset_books.py`: resets catalog to the initial state.
- `data/books.json`: editable sample catalog.
- `report/`: reading notes and screencast outline; complete the reflection after running the agent.

The orchestration tool searches, selects the first available match, and reserves it using the same catalog operations used by the two simple tools. Success/failure returns are dictionaries with an `ok` field. The Data tool does not change state; successful reservations update `data/books.json`.

## Submission

The PDF asks for a 300–400 word article/server review, source code and README, tool tests, a 5–7 minute recorded demonstration, and a 1–2 paragraph reflection. Check the written summary draft and replace generic statements with your own observations. Add your real screencast link before submitting.

## Archive notes

The archive includes the dashboard, both Colab notebooks, the agent/server, catalog, tests and report drafts. Your local `.env` file (API key) and generated Python cache files are intentionally excluded. Book reservation data is preserved from the uploaded project.

## Sources

- https://ai.google.dev/gemini-api/docs/openai/
- https://ai.google.dev/gemini-api/docs/pricing
- https://openai.github.io/openai-agents-python/models/
- https://gofastmcp.com/getting-started/quickstart
