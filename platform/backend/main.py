import json
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from pydantic import BaseModel

from src.db import execute_insert, execute_query, execute_update

app = FastAPI(title="KV Kart Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class _JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def _serialize(obj):
    return json.loads(_JSONEncoder().encode(obj))


def _is_displayable_content(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    if stripped[0] not in ("{", "["):
        return True
    if ("order_id" in stripped or "user_id" in stripped) and (
        stripped.startswith("[{") or stripped.startswith("{")
    ):
        return False
    try:
        json.loads(stripped)
        return False
    except (json.JSONDecodeError, ValueError):
        return True


def _extract_display_content(content) -> str:
    if content is None:
        return ""
    if isinstance(content, list):
        parts = []
        for block in content:
            if not isinstance(block, dict):
                continue
            text = block.get("text") or block.get("content")
            if text is None:
                continue
            s = str(text).strip()
            if not s:
                continue
            if s.startswith("{") or s.startswith("["):
                try:
                    obj = json.loads(s)
                    if isinstance(obj, dict):
                        if "message" in obj and isinstance(obj["message"], str):
                            parts.append(obj["message"])
                        elif "content" in obj and isinstance(obj["content"], str):
                            parts.append(obj["content"])
                except (json.JSONDecodeError, ValueError, TypeError):
                    parts.append(s)
            else:
                parts.append(s)
        return "\n\n".join(parts) if parts else ""
    text = content if isinstance(content, str) else str(content)
    stripped = text.strip()
    if stripped.startswith("{") and "content" in stripped:
        try:
            obj = json.loads(stripped)
            if isinstance(obj, dict) and "content" in obj:
                return obj["content"] or ""
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
    return text


_agent = None
_agent_error = None


def _get_agent():
    global _agent, _agent_error
    if _agent is not None:
        return _agent
    if _agent_error is not None:
        raise _agent_error
    try:
        from src.agents.chat import ChatAgent

        _agent = ChatAgent()
        return _agent
    except Exception as e:
        _agent_error = e
        raise


# ---------------------------------------------------------------------------
# Product endpoints
# ---------------------------------------------------------------------------


@app.get("/api/products")
def list_products(
    search: str = Query(None),
    category_id: int = Query(None),
    brand_id: int = Query(None),
    limit: int = Query(20),
    offset: int = Query(0),
):
    sql = """
        SELECT p.product_id, p.name, p.description, p.selling_price, p.base_price,
               p.discount_percent, p.stock_quantity, p.average_rating, p.total_ratings,
               p.tags, b.name AS brand_name, c.name AS category_name,
               p.category_id, p.brand_id,
               (SELECT pi.image_url FROM product_images pi
                WHERE pi.product_id = p.product_id
                ORDER BY pi.is_primary DESC, pi.sort_order LIMIT 1) AS image_url
        FROM products p
        LEFT JOIN brands b ON p.brand_id = b.brand_id
        LEFT JOIN categories c ON p.category_id = c.category_id
        WHERE p.is_active = 1
    """
    params: list = []
    if search:
        sql += " AND (p.name LIKE %s OR p.description LIKE %s OR p.tags LIKE %s)"
        params.extend([f"%{search}%"] * 3)
    if category_id:
        sql += " AND p.category_id = %s"
        params.append(category_id)
    if brand_id:
        sql += " AND p.brand_id = %s"
        params.append(brand_id)
    sql += " ORDER BY p.average_rating DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    return _serialize(execute_query(sql, params))


@app.get("/api/products/{product_id}")
def get_product(product_id: int):
    rows = execute_query(
        """SELECT p.*, b.name AS brand_name, c.name AS category_name,
           (SELECT pi.image_url FROM product_images pi
            WHERE pi.product_id = p.product_id
            ORDER BY pi.is_primary DESC, pi.sort_order LIMIT 1) AS image_url
           FROM products p
           LEFT JOIN brands b ON p.brand_id = b.brand_id
           LEFT JOIN categories c ON p.category_id = c.category_id
           WHERE p.product_id = %s""",
        [product_id],
    )
    if not rows:
        return {"error": "Product not found"}
    return _serialize(rows[0])


@app.get("/api/products/{product_id}/reviews")
def get_product_reviews(product_id: int, limit: int = Query(10)):
    return _serialize(
        execute_query(
            """SELECT r.*, u.first_name, u.last_name
               FROM product_reviews r
               LEFT JOIN users u ON r.user_id = u.user_id
               WHERE r.product_id = %s
               ORDER BY r.created_at DESC LIMIT %s""",
            [product_id, limit],
        )
    )


@app.get("/api/categories")
def list_categories():
    return _serialize(
        execute_query("SELECT * FROM categories WHERE is_active = 1 ORDER BY name")
    )


@app.get("/api/brands")
def list_brands():
    return _serialize(
        execute_query("SELECT * FROM brands WHERE is_active = 1 ORDER BY name")
    )


# ---------------------------------------------------------------------------
# User endpoints
# ---------------------------------------------------------------------------


@app.get("/api/users")
def list_users(limit: int = Query(10)):
    return _serialize(
        execute_query(
            "SELECT user_id, first_name, last_name, email "
            "FROM users WHERE account_status = 'active' LIMIT %s",
            [limit],
        )
    )


# ---------------------------------------------------------------------------
# Cart endpoints
# ---------------------------------------------------------------------------


@app.get("/api/cart/{user_id}")
def get_cart(user_id: int):
    return _serialize(
        execute_query(
            """SELECT ci.cart_item_id, ci.product_id, ci.quantity, ci.added_at,
                      p.name, p.selling_price, p.base_price, p.discount_percent,
                      p.stock_quantity, b.name AS brand_name,
                      (SELECT pi.image_url FROM product_images pi
                       WHERE pi.product_id = p.product_id
                       ORDER BY pi.is_primary DESC, pi.sort_order LIMIT 1) AS image_url
               FROM cart_items ci
               JOIN products p ON ci.product_id = p.product_id
               LEFT JOIN brands b ON p.brand_id = b.brand_id
               WHERE ci.user_id = %s
               ORDER BY ci.added_at DESC""",
            [user_id],
        )
    )


class AddToCartRequest(BaseModel):
    product_id: int
    quantity: int = 1


@app.post("/api/cart/{user_id}")
def add_to_cart(user_id: int, item: AddToCartRequest):
    existing = execute_query(
        "SELECT cart_item_id, quantity FROM cart_items WHERE user_id = %s AND product_id = %s",
        [user_id, item.product_id],
    )
    if existing:
        execute_update(
            "UPDATE cart_items SET quantity = quantity + %s WHERE cart_item_id = %s",
            [item.quantity, existing[0]["cart_item_id"]],
        )
        return {"status": "updated"}
    execute_insert(
        "INSERT INTO cart_items (user_id, product_id, quantity) VALUES (%s, %s, %s)",
        [user_id, item.product_id, item.quantity],
    )
    return {"status": "added"}


@app.delete("/api/cart/{user_id}/{cart_item_id}")
def remove_from_cart(user_id: int, cart_item_id: int):
    execute_update(
        "DELETE FROM cart_items WHERE cart_item_id = %s AND user_id = %s",
        [cart_item_id, user_id],
    )
    return {"status": "removed"}


# ---------------------------------------------------------------------------
# Orders endpoints
# ---------------------------------------------------------------------------


@app.get("/api/orders/{user_id}")
def get_user_orders(user_id: int):
    orders = execute_query(
        """SELECT o.order_id, o.order_number, o.order_status, o.placed_at,
                  o.confirmed_at, o.shipped_at, o.delivered_at
           FROM orders o WHERE o.user_id = %s ORDER BY o.placed_at DESC""",
        [user_id],
    )
    for order in orders:
        order["items"] = execute_query(
            """SELECT oi.*, p.name FROM order_items oi
               JOIN products p ON oi.product_id = p.product_id
               WHERE oi.order_id = %s""",
            [order["order_id"]],
        )
    return _serialize(orders)


# ---------------------------------------------------------------------------
# Chat endpoint (SSE streaming)
# ---------------------------------------------------------------------------


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []
    user_id: int
    thread_id: str | None = None


def _build_history(request: ChatRequest):
    history: list[BaseMessage] = []
    for msg in request.history:
        if msg.get("role") == "user":
            history.append(HumanMessage(content=msg["content"]))
        else:
            history.append(AIMessage(content=msg["content"]))
    return history


@app.post("/api/chat/sync")
def chat_sync(request: ChatRequest):
    """Non-streaming chat endpoint that returns a plain JSON response."""
    agent = _get_agent()
    history = _build_history(request)
    thread_id = request.thread_id or f"user_{request.user_id}"
    result = agent.chat(
        request.message,
        thread_id,
        request.user_id,
        history=history,
    )
    messages = (
        result.get("messages", [])
        if isinstance(result, dict)
        else getattr(result, "messages", [])
    )
    for msg in reversed(messages):
        content = getattr(msg, "content", None) or (
            msg.get("content") if isinstance(msg, dict) else None
        )
        role = getattr(msg, "type", None) or (
            msg.get("type") if isinstance(msg, dict) else None
        )
        if content and role == "ai":
            return {"response": _extract_display_content(content)}
    return {"response": ""}


@app.post("/api/chat")
def chat(request: ChatRequest):
    agent = _get_agent()
    history = _build_history(request)

    thread_id = request.thread_id or f"user_{request.user_id}"

    def generate():
        full_response = ""
        final_content = None
        try:
            for chunk in agent.stream(
                request.message,
                thread_id,
                request.user_id,
                history=history,
            ):
                if not isinstance(chunk, tuple) or len(chunk) != 2:
                    continue
                mode, data = chunk

                if mode == "messages":
                    part = data[0] if isinstance(data, (list, tuple)) else data
                    meta = (
                        data[1]
                        if isinstance(data, (list, tuple)) and len(data) >= 2
                        else {}
                    )
                    node = meta.get("langgraph_node")
                    if node == "intent_agent":
                        continue
                    if node not in (
                        "order_management_agent",
                        "product_discovery_agent",
                        "general_assistant_agent",
                    ):
                        continue
                    if isinstance(part, BaseMessage) and part.content:
                        text = _extract_display_content(part.content)
                        if text.strip() and _is_displayable_content(text):
                            if not full_response.endswith(text):
                                full_response += text
                                yield f"data: {json.dumps({'type': 'token', 'content': text})}\n\n"

                elif mode == "updates" and isinstance(data, dict):
                    for node_output in data.values():
                        if not isinstance(node_output, dict):
                            continue
                        if node_output.get("intent") is not None:
                            yield f"data: {json.dumps({'type': 'status', 'intent': str(node_output['intent'])})}\n\n"
                        for msg in node_output.get("messages") or []:
                            if isinstance(msg, AIMessage) and msg.tool_calls:
                                for tc in msg.tool_calls:
                                    yield f"data: {json.dumps({'type': 'tool_call', 'name': tc.get('name', 'tool')})}\n\n"
                            elif isinstance(msg, ToolMessage):
                                pass
                            elif isinstance(msg, AIMessage) and msg.content:
                                final_content = _extract_display_content(msg.content)

            done_content = None
            if not full_response:
                raw = final_content if final_content is not None else ""
                done_content = _extract_display_content(raw) or None
            yield f"data: {json.dumps({'type': 'done', 'content': done_content})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/health")
def health():
    return {"status": "ok"}


# Serve the built frontend if available (Docker build copies it to platform/static/)
_static_dir = Path(__file__).resolve().parent.parent / "static"
if _static_dir.is_dir():
    assets_dir = _static_dir / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """SPA catch-all: serve index.html for any non-API route."""
        return FileResponse(_static_dir / "index.html")


if __name__ == "__main__":
    import uvicorn

    # workers=1 required: chat uses in-memory checkpointer (MemorySaver);
    # multi-worker would lose conversation state per thread_id
    uvicorn.run(app, host="0.0.0.0", port=8081, workers=1)
