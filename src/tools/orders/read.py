
from langchain_core.tools import tool

from src.db import execute_query


@tool
def get_order_by_order_number(order_number: str) -> dict:
    """Retrieve a single order by its customer-facing order number (e.g. 'ORD-12345').

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
        return {"error": f"No order found with order number '{order_number}'."}
    return rows[0]


@tool
def get_order_by_id(order_id: int) -> dict:
    """Retrieve a single order by its internal order ID.

    Use this when you already have the numeric order_id from another query.

    Args:
        order_id: The internal numeric order identifier.
    """
    rows = execute_query(
        "SELECT * FROM orders WHERE order_id = %s",
        (order_id,),
    )
    if not rows:
        return {"error": f"No order found with order_id {order_id}."}
    return rows[0]


@tool
def get_orders_by_user(user_id: int, status_filter: str | None = None) -> list:
    """Get all orders placed by a specific user, newest first.

    Optionally filter by order status (e.g. 'delivered', 'shipped', 'cancelled').
    Returns a list of order summaries. Limited to last 50 orders.

    Args:
        user_id: The customer's user ID.
        status_filter: Optional order status to filter by
            (pending, confirmed, processing, shipped, out_for_delivery,
             delivered, cancelled, return_requested, returned, failed).
    """
    if status_filter:
        valid_statuses = {
            "pending", "confirmed", "processing", "shipped",
            "out_for_delivery", "delivered", "cancelled",
            "return_requested", "returned", "failed",
        }
        if status_filter not in valid_statuses:
            return {"error": f"Invalid status '{status_filter}'. Valid: {sorted(valid_statuses)}"}
        rows = execute_query(
            "SELECT * FROM orders WHERE user_id = %s AND order_status = %s "
            "ORDER BY placed_at DESC LIMIT 50",
            (user_id, status_filter),
        )
    else:
        rows = execute_query(
            "SELECT * FROM orders WHERE user_id = %s "
            "ORDER BY placed_at DESC LIMIT 50",
            (user_id,),
        )
    if not rows:
        return {"message": "No orders found for this user."}
    return rows


@tool
def get_order_items(order_id: int) -> list:
    """Get all line items for a given order, including product names and prices.

    Joins with the products table to include product name and current details
    alongside the ordered quantity and price at time of purchase.

    Args:
        order_id: The internal numeric order identifier.
    """
    rows = execute_query(
        """
        SELECT oi.order_item_id, oi.order_id, oi.product_id, oi.quantity,
               oi.unit_price, oi.total_price, oi.item_status,
               p.name AS product_name, p.selling_price AS current_price,
               p.is_active AS product_active
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        WHERE oi.order_id = %s
        """,
        (order_id,),
    )
    if not rows:
        return {"message": f"No items found for order_id {order_id}."}
    return rows


@tool
def get_order_details_full(order_number: str) -> dict:
    """Get a comprehensive order summary: order info, line items, payment, and shipment.

    This is the most complete view of an order — use it when a customer asks
    'What is the status of my order?' or needs a full breakdown.

    Args:
        order_number: The customer-facing order number string.
    """
    # Fetch order
    order_rows = execute_query(
        "SELECT * FROM orders WHERE order_number = %s",
        (order_number,),
    )
    if not order_rows:
        return {"error": f"No order found with order number '{order_number}'."}

    order = order_rows[0]
    order_id = order["order_id"]

    # Fetch items
    items = execute_query(
        """
        SELECT oi.order_item_id, oi.product_id, oi.quantity,
               oi.unit_price, oi.total_price, oi.item_status,
               p.name AS product_name
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        WHERE oi.order_id = %s
        """,
        (order_id,),
    )

    # Fetch payment
    payments = execute_query(
        "SELECT * FROM payments WHERE order_id = %s",
        (order_id,),
    )

    # Fetch shipment
    shipments = execute_query(
        """
        SELECT s.*, lp.name AS logistics_partner_name
        FROM shipments s
        JOIN logistics_partners lp ON s.logistics_partner_id = lp.partner_id
        WHERE s.order_id = %s
        """,
        (order_id,),
    )

    return {
        "order": order,
        "items": items,
        "payment": payments[0] if payments else None,
        "shipment": shipments[0] if shipments else None,
    }


@tool
def get_bulk_orders_by_ids(order_ids: list[int]) -> list:
    """Retrieve multiple orders at once by their internal order IDs.

    Useful when you need details for several orders in a single call
    (e.g. comparing orders or building a summary).
    Limited to 20 order IDs per call.

    Args:
        order_ids: A list of numeric order IDs (max 20).
    """
    if not order_ids:
        return {"error": "order_ids list cannot be empty."}
    if len(order_ids) > 20:
        return {"error": "Cannot fetch more than 20 orders at once."}

    placeholders = ",".join(["%s"] * len(order_ids))
    rows = execute_query(
        f"SELECT * FROM orders WHERE order_id IN ({placeholders}) "
        f"ORDER BY placed_at DESC",
        tuple(order_ids),
    )
    return rows
