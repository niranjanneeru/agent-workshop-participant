from langchain_core.tools import tool

from src.db import execute_query


@tool
def get_payment_by_order(order_id: int) -> dict:
    """Get payment details for a specific order.

    Returns payment method, gateway, transaction ID, amount, status,
    and timestamps. Useful when a customer asks about payment confirmation.

    Args:
        order_id: The internal order ID.
    """
    rows = execute_query(
        "SELECT * FROM payments WHERE order_id = %s",
        (order_id,),
    )
    if not rows:
        return {"message": f"No payment record found for order_id {order_id}."}
    return rows[0]


@tool
def get_payments_by_user(user_id: int) -> list:
    """Get all payment records for a user, most recent first.

    Returns a list of payment summaries including order ID, method, amount,
    and status. Limited to last 50 payments.

    Args:
        user_id: The customer's user ID.
    """
    rows = execute_query(
        """
        SELECT p.payment_id, p.order_id, p.payment_method, p.payment_gateway,
               p.amount, p.currency, p.payment_status, p.paid_at, p.created_at,
               o.order_number
        FROM payments p
        JOIN orders o ON p.order_id = o.order_id
        WHERE p.user_id = %s
        ORDER BY p.created_at DESC
        LIMIT 50
        """,
        (user_id,),
    )
    if not rows:
        return {"message": "No payment records found for this user."}
    return rows


@tool
def get_bulk_payments_by_orders(order_ids: list[int]) -> list:
    """Retrieve payment details for multiple orders at once.

    Useful when building a summary of payments across several orders.
    Limited to 20 order IDs per call.

    Args:
        order_ids: List of order IDs (max 20).
    """
    if not order_ids:
        return {"error": "order_ids list cannot be empty."}
    if len(order_ids) > 20:
        return {"error": "Cannot fetch more than 20 payment records at once."}

    placeholders = ",".join(["%s"] * len(order_ids))
    rows = execute_query(
        f"""
        SELECT p.*, o.order_number
        FROM payments p
        JOIN orders o ON p.order_id = o.order_id
        WHERE p.order_id IN ({placeholders})
        ORDER BY p.created_at DESC
        """,
        tuple(order_ids),
    )
    return rows
