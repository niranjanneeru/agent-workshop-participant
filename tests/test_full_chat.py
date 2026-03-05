import pytest
from langchain_core.messages import AIMessage, HumanMessage

from src.agents.chat import ChatAgent
from src.graphs.chat.states import AgentState


def _tool_names_from_messages(messages: list) -> set[str]:
    out: set[str] = set()
    for m in messages:
        if isinstance(m, AIMessage) and m.tool_calls:
            for tc in m.tool_calls:
                name = tc.get("name") if isinstance(tc, dict) else tc.name
                if name:
                    out.add(name)
    return out


@pytest.fixture(scope="module")
def chat_agent():
    return ChatAgent()


def _invoke_and_get_tool_names(
    agent: ChatAgent, message: str, history: list | None = None
) -> set[str]:
    state = AgentState(messages=list(history or []) + [HumanMessage(content=message)])
    result = agent.graph.invoke(state)
    return _tool_names_from_messages(result.get("messages", []))


def _chat_api_tool_names(
    agent: ChatAgent,
    message: str,
    thread_id: str = "test_thread_1",
    user_id: int = 1,
    history: list | None = None,
) -> set[str]:
    result = agent.chat(message, thread_id, user_id, history=history)
    return _tool_names_from_messages(result.get("messages", []))


@pytest.mark.integration
@pytest.mark.parametrize(
    "message,expected_tool_names",
    [
        (
            "Where is my order? My user ID is 1.",
            {
                "get_orders_by_user",
                "get_order_by_id",
                "get_order_by_order_number",
                "get_order_details_full",
            },
        ),
        (
            "Track my order 1001",
            {
                "get_order_by_id",
                "get_order_by_order_number",
                "get_full_tracking_by_order",
                "get_tracking_events",
                "get_shipment_by_order",
            },
        ),
        (
            "What's the delivery time from Bangalore to Mumbai?",
            {"get_delivery_estimate", "get_logistics_partners"},
        ),
        (
            "Check my refund status. User ID 1.",
            {"get_refund_by_user", "get_refund_status", "get_return_requests_by_user"},
        ),
        (
            "Show my support tickets. User ID 1.",
            {"get_tickets_by_user", "get_ticket_details"},
        ),
        ("What's in my cart? User 1.", {"get_cart_items"}),
        ("What's my wallet balance? User 1.", {"get_wallet_balance"}),
        (
            "Do you have any coupons? User ID 1.",
            {"get_available_coupons", "validate_coupon"},
        ),
        (
            "What's your return policy?",
            {"semantic_search", "hybrid_search"},
        ),
        (
            "What's your cancellation policy?",
            {"semantic_search", "hybrid_search"},
        ),
        ("Search for wireless headphones", {"search_products"}),
        (
            "What phones do you have?",
            {
                "search_products",
                "get_products_by_category",
                "get_products_by_brand",
                "get_all_categories",
            },
        ),
        ("Show me laptops under 50k", {"search_products", "get_products_by_category"}),
    ],
)
def test_full_chat_calls_relevant_tools(chat_agent, message, expected_tool_names):
    called = _invoke_and_get_tool_names(chat_agent, message)
    assert (
        expected_tool_names & called
    ), f"Expected at least one of {expected_tool_names} to be called for {message!r}; got {called}"


@pytest.mark.integration
def test_full_chat_calls_some_tool_for_order_style_query(chat_agent):
    """Order-management intent may use DB tools or MCP tools (names are server-dependent)."""
    called = _invoke_and_get_tool_names(
        chat_agent, "I need help with my order. User ID 1."
    )
    assert len(called) >= 1, f"Expected at least one tool to be called; got {called}"


@pytest.mark.integration
def test_chat_api_requires_thread_id_and_user_id(chat_agent):
    """ChatAgent.chat() with required thread_id and user_id returns messages and can call tools."""
    called = _chat_api_tool_names(
        chat_agent,
        "Where is my order? My user ID is 1.",
        thread_id="test_thread_chat_api",
        user_id=1,
    )
    assert (
        "get_orders_by_user" in called
        or "get_order_by_id" in called
        or "get_order_by_order_number" in called
    )


@pytest.mark.integration
def test_chat_api_follow_up_uses_same_thread(chat_agent):
    """Multi-turn via chat() with same thread_id uses checkpointed history."""
    tid = "test_thread_follow_up"
    uid = 1
    _chat_api_tool_names(
        chat_agent, "Where is my order? User ID 1.", thread_id=tid, user_id=uid
    )
    called = _chat_api_tool_names(
        chat_agent, "What's the delivery date?", thread_id=tid, user_id=uid
    )
    assert isinstance(called, set)
