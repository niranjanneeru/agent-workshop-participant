from fastmcp import FastMCP

from src.config import settings

mcp = FastMCP("MCP")


@mcp.tool()
def send_order_update_email(order_number: str, message: str) -> dict:
    """Send an order status update to the customer by email.

    Use when the customer asks to receive order updates by email (e.g. when it ships).

    Args:
        order_number: The order number (e.g. KV-20250210-0018).
        message: Short update message to send (e.g. "Your order has shipped.").
    """
    return {
        "success": True,
        "channel": "email",
        "order_number": order_number,
        "message": message[:500],
        "status": "sent",
    }


@mcp.tool()
def send_order_update_whatsapp(order_number: str, message: str) -> dict:
    """Send an order status update to the customer by WhatsApp.

    Use when the customer asks to receive order updates on WhatsApp (e.g. when it ships).

    Args:
        order_number: The order number (e.g. KV-20250210-0018).
        message: Short update message to send (e.g. "Your order has shipped.").
    """
    return {
        "success": True,
        "channel": "whatsapp",
        "order_number": order_number,
        "message": message[:500],
        "status": "sent",
    }


if __name__ == "__main__":
    mcp.run(
        transport="sse",
        host=settings.MCP_HOST,
        port=settings.MCP_PORT,
    )
