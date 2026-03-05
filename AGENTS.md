# Agent Development Guide

For the workshop step order, see [PLAN.md](PLAN.md).

Guide for building agents in this workshop with LangGraph.

## Architecture

```
Agents (src/agents/)  →  Graphs (src/graphs/)  →  Tools (src/tools/)
```

- **Graphs**: LangGraph workflows (state, nodes, conditional edges). One graph per directory under `src/graphs/<name>/`.
- **Agents**: Thin wrappers that hold a graph and expose `chat()`, `stream()`, `achat()`, `astream()`.
- **Tools**: Reusable LangChain tools (catalog, RAG, web search, MCP). Used inside graph nodes.

## Folder structure (agent-related)

```
src/
├── agents/           # ChatAgent, etc. — wrap graphs, expose chat/stream
├── graphs/           # One dir per graph
│   └── chat/        # states.py, nodes.py, builder.py
├── tools/           # orders, products, RAG, search (Tavily), mcp (MCP client)
├── mcp/             # MCP server (Docker); e.g. get_delivery_between_coordinates
├── vector_db/       # Weaviate for RAG (external embeddings)
├── embedding/       # OpenAI embeddings
└── config.py        # settings from .env
```

## Building an agent with LangGraph

### 1. State (`src/graphs/<name>/states.py`)

```python
from typing import Annotated
from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from pydantic import BaseModel

class AgentState(BaseModel):
    messages: Annotated[list[AnyMessage], add_messages]
```
Add more fields if needed (e.g. `intent` for routing, or guardrail flags like `user_guardrail_flag` and `agent_response_safe`).

### 2. Nodes (`src/graphs/<name>/nodes.py`)

Each node is a function `(state) -> state_updates` (dict). Use LLM + tools here (e.g. `create_agent` from LangChain with a tool list).

### 3. Builder (`src/graphs/<name>/builder.py`)

```python
from langgraph.graph import StateGraph, END
from src.graphs.<name>.states import AgentState
from src.graphs.<name>.nodes import intent_node, order_node, product_node

def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("intent", intent_node)
    workflow.add_node("order", order_node)
    workflow.add_node("product", product_node)
    workflow.set_entry_point("intent")
    workflow.add_conditional_edges("intent", route_by_intent, {"order": "order", "product": "product", ...})
    workflow.add_edge("order", END)
    workflow.add_edge("product", END)
    return workflow.compile()
```

### 4. Agent (`src/agents/<name>.py`)

```python
from langchain_core.messages import HumanMessage
from src.graphs.<name>.builder import build_graph
from src.graphs.<name>.states import AgentState

class YourAgent:
    def __init__(self):
        self.graph = build_graph()

    def chat(self, message: str, history=None) -> dict:
        state = AgentState(messages=(history or []) + [HumanMessage(content=message)])
        return self.graph.invoke(state)

    def stream(self, message: str, history=None):
        state = AgentState(messages=(history or []) + [HumanMessage(content=message)])
        yield from self.graph.stream(state, stream_mode=["messages", "updates"])
```

## Tools

- **Add a tool**: Implement in `src/tools/` (e.g. `@tool` with type hints and docstring), export from `src/tools/__init__.py`. Bind the tool list to the agent in the graph’s nodes (e.g. `create_agent(model, tools=...)`).
- **Catalog**: Orders, products, logistics, payments, returns, support, coupons, wallet, notifications, users, cart, wishlist — in `src/tools/`, used by order-management agent.
- **RAG**: `create_rag_tools(vector_db, embedding)` in `src/tools/rag/search.py`; semantic/hybrid search over ingested docs. Ingest: put files in `data/`, runs on `docker compose up`.
- **Web search**: `get_web_search_tools()` from `src/tools/search/` (Tavily); used by product-discovery agent.
- **MCP**: `get_mcp_tools()` loads tools from the MCP server (`MCP_URL`); used by order-management agent (e.g. delivery estimates).

### Writing a tool (reference pattern)

Each tool domain lives in `src/tools/<domain>/` with `__init__.py` re-exporting, and `read.py`/`write.py` for the implementations. DB tools query MySQL via `src.db.execute_query`.

```
src/tools/<domain>/
├── __init__.py    # re-exports: from src.tools.<domain>.read import *
├── read.py        # read-only tools (@tool)
└── write.py       # write tools (@tool) — optional
```

**Tool template (DB tool using MySQL):**

```python
from langchain_core.tools import tool
from src.db import execute_query

@tool
def get_order_by_order_number(order_number: str) -> dict:
    """Retrieve a single order by its customer-facing order number (e.g. ‘ORD-12345’).

    Use this when the customer provides their order number.
    Returns order details including status, amounts, and timestamps.

    Args:
        order_number: The unique order number string shown to customers.
    """
    rows = execute_query(
        "SELECT * FROM orders WHERE order_number = %s",
        (order_number,),
    )
    if not rows:
        return {"error": f"No order found with order number ‘{order_number}’."}
    return rows[0]
```

**Key rules:**
- Use `@tool` decorator from `langchain_core.tools`
- Type-hint all parameters and return type
- Write a clear docstring (the LLM reads it to decide when/how to call the tool)
- Use `execute_query(sql, params)` for reads, `execute_insert`/`execute_update` for writes
- Always use parameterized queries (`%s`) — never f-strings in SQL
- Return dicts or lists; include `{"error": ...}` on failures

**Re-export in `__init__.py`:**

```python
from src.tools.<domain>.read import (
    get_order_by_order_number,
    get_order_by_id,
)
```

Then add the tools to the grouped list in `src/tools/__init__.py`.

## Chat graph (reference)

- **State**: `src/graphs/chat/states.py` (messages, intent, user_guardrail_flag, agent_response_safe).
- **Nodes**: `src/graphs/chat/nodes.py` — user_guardrails_agent, intent_agent, order_management_agent (catalog + RAG + MCP), product_discovery_agent (catalog + web search), general_assistant_agent, agent_guardrails_agent.
- **Builder**: `src/graphs/chat/builder.py` — user_guardrails → intent → domain/general → agent_guardrails → END.
- **Agent**: `src/agents/chat.py` — `ChatAgent` with `chat`, `stream`, etc.

Prompts live in `src/graphs/chat/prompts.py`. Order management uses `order_management_tools` + MCP + RAG; product discovery uses `product_discovery_tools` + web search.

### Guardrails architecture

- **User guardrails** (first node): Checks user input for safety/scope using structured output (`content`, `flag`). If flagged, writes refusal and routes directly to END.
- **Agent guardrails** (last node): Validates agent response and masks PII via LLM. Uses structured output (`content`, `flag`). If flagged, replaces with "Something went wrong"; otherwise returns PII-masked response.

## RAG in agents

- **Ingest**: `scripts/ingest.py` loads `data/` (.txt, .md, .pdf), chunks, embeds (OpenAI via LiteLLM), writes to Weaviate. Runs on `docker compose up`.
- **In the agent**: RAG tools are created in the order-management node with `WeaviateVectorDB(url=settings.WEAVIATE_URL)` and `OpenAIEmbedding()` (embeddings use `LITELLM_URL`). Pass `create_rag_tools(vector_db, embedding)` into the tool list so the LLM can call `semantic_search` / `hybrid_search`.

## Best practices

- **State**: Minimal; use `Annotated` + reducers (e.g. `add_messages`) for message lists.
- **Nodes**: Single responsibility; handle errors inside the node.
- **Agents**: Same interface (`chat`, `stream`) so the Streamlit UI can stay generic.
- **Tools**: Type hints, docstrings; reuse across agents where it makes sense.

## Environment

Config is loaded from `.env` via `src.config.settings` (pydantic-settings). Required: `OPENAI_API_KEY`, `LITELLM_URL`, `TAVILY_API_KEY`, `MCP_URL`. Optional: `WEAVIATE_URL`, `MCP_HOST`, `MCP_PORT`, `OPENAI_LLM_MODEL`, `OPENAI_EMBEDDING_MODEL`, `LANGSMITH_TRACING`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`. See `env_sample`.

## Testing

| File | What it covers |
|------|----------------|
| `test_db_tools.py` | DB tools (MySQL): orders, products, logistics, payments, returns, support, coupons, wallet, notifications, users, cart, wishlist |
| `test_chat_intent.py` | Intent classification (single-turn and follow-up) |
| `test_full_chat.py` | Full chat: expected tools called for orders, delivery, refunds, support, cart, wallet, coupons, RAG, product search |
| `test_rag.py` | RAG: Weaviate + embeddings, semantic/hybrid search, get_document_by_id |
| `test_web_search.py` | Web search (Tavily) |

`uv sync --extra dev` then `uv run python -m pytest tests/ -v`

## Adding a new agent

Create `src/graphs/<name>/` (states, nodes, builder), add a class in `src/agents/`, add tools in `src/tools/` if needed, wire the agent in `app.py`, add tests, update this doc.

## Resources

- [LangGraph](https://langchain-ai.github.io/langgraph/) · [LangChain Tools](https://python.langchain.com/docs/modules/tools/) · [Pydantic](https://docs.pydantic.dev/) · [Streamlit](https://docs.streamlit.io/) · [Weaviate](https://weaviate.io/developers/weaviate/)
