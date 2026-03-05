import pytest
from langchain_core.messages import HumanMessage

from src.agents.chat import ChatAgent
from src.graphs.chat.states import AgentState, Intent

SINGLE_TURN = [
    ("Hi there!", Intent.GENERAL),
    ("Hello!", Intent.GENERAL),
    ("Thanks for your help", Intent.GENERAL),
    ("Bye", Intent.GENERAL),
    ("What can you help me with?", Intent.GENERAL),
    ("Ok", Intent.GENERAL),
    ("Where is my order? My user ID is 1.", Intent.ORDER_MANAGEMENT),
    ("Track my order 1001", Intent.ORDER_MANAGEMENT),
    ("What's the delivery time from Bangalore to Mumbai?", Intent.ORDER_MANAGEMENT),
    ("I want to cancel my order. User ID 1.", Intent.ORDER_MANAGEMENT),
    ("I need to return an item. Order delivered last week.", Intent.ORDER_MANAGEMENT),
    ("Check my refund status for order 1002", Intent.ORDER_MANAGEMENT),
    ("Do you have any coupons for me? User ID 1.", Intent.ORDER_MANAGEMENT),
    ("What's my wallet balance? User 1.", Intent.ORDER_MANAGEMENT),
    ("I want to raise a support ticket", Intent.ORDER_MANAGEMENT),
    ("What's your return policy?", Intent.ORDER_MANAGEMENT),
    ("What phones do you have?", Intent.PRODUCT_DISCOVERY),
    ("Show me laptops under 50k", Intent.PRODUCT_DISCOVERY),
    ("Search for wireless headphones", Intent.PRODUCT_DISCOVERY),
    ("What's in the electronics category?", Intent.PRODUCT_DISCOVERY),
    ("Recommend a good smartphone", Intent.PRODUCT_DISCOVERY),
    ("Add the last one to my cart. User ID 1.", Intent.PRODUCT_DISCOVERY),
    ("Show me Samsung TVs", Intent.PRODUCT_DISCOVERY),
]

FOLLOW_UP_TURNS = [
    (
        ["Where is my order? User ID 1.", "And the delivery date?"],
        Intent.ORDER_MANAGEMENT,
    ),
    (
        ["What phones do you have?", "Show me the cheapest one"],
        Intent.PRODUCT_DISCOVERY,
    ),
    (
        ["Hi", "Actually I wanted to check my order status. User 1."],
        Intent.ORDER_MANAGEMENT,
    ),
    (["I need help with a return.", "My order ID is 1001"], Intent.ORDER_MANAGEMENT),
    (
        [
            "Search for bluetooth speakers",
            "Add the first result to my wishlist. User 1.",
        ],
        Intent.PRODUCT_DISCOVERY,
    ),
]


@pytest.fixture(scope="module")
def chat_agent():
    return ChatAgent()


def _invoke_intent(agent: ChatAgent, messages: list[str]) -> Intent | None:
    history = [HumanMessage(content=m) for m in messages[:-1]]
    last = messages[-1]
    state = AgentState(messages=history + [HumanMessage(content=last)])
    result = agent.graph.invoke(state)
    return result.get("intent")


@pytest.mark.parametrize("message,expected_intent", SINGLE_TURN)
def test_single_turn_intent(chat_agent, message, expected_intent):
    got = _invoke_intent(chat_agent, [message])
    assert got == expected_intent, f"message={message!r}"


@pytest.mark.parametrize("messages,expected_intent", FOLLOW_UP_TURNS)
def test_follow_up_intent(chat_agent, messages, expected_intent):
    got = _invoke_intent(chat_agent, messages)
    assert got == expected_intent, f"messages={messages!r}"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
