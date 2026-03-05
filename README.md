# Agent Development Workshop

Workshop: start from tag `checkpoint-0` and follow [PLAN.md](PLAN.md); see [AGENTS.md](AGENTS.md) for implementation reference.

## Quick Start

**Prerequisites:** [Docker](https://docs.docker.com/get-docker/), [Docker Compose](https://docs.docker.com/compose/install/). Optional: Node 20+ and Yarn for platform frontend.

1. Clone and enter the repo:
   ```bash
   git clone <repository-url>
   cd agent-development-workshop
   ```

2. Set up environment:
   ```bash
   cp env_sample .env
   ```
   Edit `.env`: set `OPENAI_API_KEY`, `LITELLM_URL`, `TAVILY_API_KEY`, and `MCP_URL` (e.g. `http://mcp:8000` when using Docker). Optional: enable LangSmith tracing with `LANGSMITH_TRACING=true` and `LANGSMITH_API_KEY`.

3. (Optional) Platform frontend: `cd platform/frontend && yarn && yarn build`

4. Start the stack: `docker compose up -d`

5. Open the services (see URLs below).

Ingestion runs on each `docker compose up`. For full behaviour (orders, catalog, etc.) the stack includes MySQL.

## URLs

| Service | URL |
|---------|-----|
| **Streamlit** (chat UI) | http://localhost:8501 |
| **Platform** (e-commerce frontend + API) | http://localhost:8081 |
| **Evaluation** (agent evaluation UI) | http://localhost:3000 |
| **Adminer** (DB admin) | http://localhost:8080 |
| **Weaviate** (vector DB) | http://localhost:8090 |

---

## Project Structure

```
├── app.py                 # Streamlit chat UI
├── src/
│   ├── agents/            # Agent interfaces (e.g. ChatAgent)
│   ├── graphs/            # LangGraph workflows (intent, order management, product discovery)
│   ├── tools/             # Catalog, RAG, web search, MCP client
│   ├── mcp/               # MCP server (Docker service)
│   ├── vector_db/         # Weaviate for RAG
│   └── embedding/         # OpenAI embeddings
├── scripts/ingest.py      # Ingest data/ into Weaviate
├── data/                  # Documents for RAG
├── tests/                 # test_db_tools, test_chat_intent, test_full_chat, test_rag, test_web_search
└── docker-compose.yml
```

---

## Development

**Common commands**

- Start: `docker compose up -d`
- Stop: `docker compose down`
- Logs: `docker compose logs -f streamlit` (or `platform`, `evaluation`)
- Rebuild: `docker compose build --no-cache`
- Platform frontend: `cd platform/frontend && yarn build` or `yarn dev`
- Tests: `uv sync --extra dev` then `uv run python -m pytest tests/ -v`

**Using the chat**

The chat includes dual guardrails: user guardrails (input validation/safety) and agent guardrails (response validation + PII masking). The intent agent routes each message to order management (orders, tracking, returns, payments, support, MCP), product discovery (catalog + web search), or general. Try e.g. "Where is my order?" or "What phones do you have?". Responses stream when supported.

**Local run (no Docker)**

Install [uv](https://github.com/astral-sh/uv), then:

```bash
uv sync
# set .env as above
uv run streamlit run app.py
```

---

## Troubleshooting

- **Port 8501 in use** — Change in `docker-compose.yml`, e.g. `ports: ["8502:8501"]`, or free the port.
- **Container won’t start** — Ensure Docker is running; try `docker compose build --no-cache`.
- **Hot-reload not working** — `docker compose restart streamlit` or check volume mount.
- **Platform UI not accessible outside Cursor** — If using Cursor with a remote/Dev Container:
  1. Open the **Ports** panel (View → Ports, or the "PORTS" tab in the bottom panel).
  2. Find port **8081** and ensure it's forwarded.
  3. Click **Open in Browser** or use the forwarded URL (e.g. `https://xxx-8081.app.github.dev` in Codespaces).
  4. Alternatively, try `http://127.0.0.1:8081` or `http://localhost:8081` in your system browser.

---

For architecture, RAG/Weaviate usage, and adding agents/tools, see [AGENTS.md](./AGENTS.md).
