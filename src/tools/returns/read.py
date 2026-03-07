from langchain_core.tools import tool

from src.db import execute_query


@tool
def get_return_requests_by_order(order_id: int) -> list:
    """Get all return requests for a specific order.

    Returns return reason, status, pickup date, and resolution details.
    Includes the product name for each returned item.

    Args:
        order_id: The internal order ID.
    """
    rows = execute_query(
        """
        SELECT rr.*, p.name AS product_name
        FROM return_requests rr
        JOIN order_items oi ON rr.order_item_id = oi.order_item_id
        JOIN products p ON oi.product_id = p.product_id
        WHERE rr.order_id = %s
        ORDER BY rr.requested_at DESC
        """,
        (order_id,),
    )
    if not rows:
        return {"message": f"No return requests found for order_id {order_id}."}
    return rows


@tool
def get_return_requests_by_user(user_id: int) -> list:
    """Get all return requests submitted by a user, most recent first.

    Useful for showing a customer their return history. Limited to 30 records.

    Args:
        user_id: The customer's user ID.
    """
    rows = execute_query(
        """
        SELECT rr.*, o.order_number, p.name AS product_name
        FROM return_requests rr
        JOIN orders o ON rr.order_id = o.order_id
        JOIN order_items oi ON rr.order_item_id = oi.order_item_id
        JOIN products p ON oi.product_id = p.product_id
        WHERE rr.user_id = %s
        ORDER BY rr.requested_at DESC
        LIMIT 30
        """,
        (user_id,),
    )
    if not rows:
        return {"message": "No return requests found for this user."}
    return rows


@tool
def get_refund_by_order(order_id: int) -> list:
    """Get all refund records associated with an order.

    Returns refund type, amount, method, status, and expected completion date.

    Args:
        order_id: The internal order ID.
    """
    rows = execute_query(
        "SELECT * FROM refunds WHERE order_id = %s ORDER BY initiated_at DESC",
        (order_id,),
    )
    if not rows:
        return {"message": f"No refunds found for order_id {order_id}."}
    return rows


@tool
def get_refund_by_user(user_id: int) -> list:
    """Get all refund records for a user, most recent first.

    Includes order number for reference. Limited to 30 records.

    Args:
        user_id: The customer's user ID.
    """
    rows = execute_query(
        """
        SELECT r.*, o.order_number
        FROM refunds r
        JOIN orders o ON r.order_id = o.order_id
        WHERE r.user_id = %s
        ORDER BY r.initiated_at DESC
        LIMIT 30
        """,
        (user_id,),
    )
    if not rows:
        return {"message": "No refunds found for this user."}
    return rows


@tool
def get_refund_status(refund_id: int) -> dict:
    """Check the current status of a specific refund.

    Returns detailed refund info including method, amount, expected and
    actual completion dates, and transaction reference.

    Args:
        refund_id: The refund identifier.
    """
    rows = execute_query(
        """
        SELECT r.*, o.order_number
        FROM refunds r
        JOIN orders o ON r.order_id = o.order_id
        WHERE r.refund_id = %s
        """,
        (refund_id,),
    )
    if not rows:
        return {"error": f"No refund found with refund_id {refund_id}."}
    return rows[0]
