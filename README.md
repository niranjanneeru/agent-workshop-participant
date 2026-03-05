# Agent Workshop

Workshop: start from `main` branch and follow [PLAN.md](PLAN.md); see [AGENTS.md](AGENTS.md) for implementation reference.

## Quick Start

**Prerequisites:** [Docker](https://docs.docker.com/get-docker/), [Docker Compose](https://docs.docker.com/compose/install/).

1. Clone and enter the repo:
   ```bash
   git clone <repository-url>
   cd agent-workshop
   ```

2. Set up environment:
   ```bash
   cp env_sample .env
   ```
   Edit `.env`: set `OPENAI_API_KEY`. Optional: set `LITELLM_URL`, enable LangSmith tracing.

3. Start the stack:
   ```bash
   docker compose up -d
   ```

4. Open http://localhost:8501 — you should see the chat UI.

## URLs

| Service | URL |
|---------|-----|
| **Streamlit** (chat UI) | http://localhost:8501 |
| **Platform** (e-commerce frontend + API) | http://localhost:8081 |
| **Evaluation** (agent evaluation UI) | http://localhost:3000 |
| **Adminer** (DB admin) | http://localhost:8080 |

## Development

- Start: `docker compose up -d`
- Stop: `docker compose down`
- Logs: `docker compose logs -f streamlit`
- Rebuild: `docker compose build --no-cache`
- Tests: `uv sync --extra dev` then `uv run python -m pytest tests/ -v`
