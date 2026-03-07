from datetime import datetime, timezone

from langchain_core.tools import tool

from src.db import execute_query, execute_update


# Valid state transitions for orders
_ORDER_TRANSITIONS = {
    "pending": {"confirmed", "cancelled", "failed"},
    "confirmed": {"processing", "cancelled"},
    "processing": {"shipped", "cancelled"},
    "shipped": {"out_for_delivery"},
    "out_for_delivery": {"delivered", "failed"},
    "delivered": {"return_requested"},
    "return_requested": {"returned"},
}

_CANCELLABLE_STATUSES = {"pending", "confirmed", "processing"}


@tool
def cancel_order(order_id: int, reason: str) -> dict:
    """Cancel an order if it is still eligible for cancellation.

    Business rules enforced:
    - Order must have is_cancellable = 1.
    - Order status must be one of: pending, confirmed, processing.
    - Orders that are already shipped, delivered, or cancelled cannot be cancelled.

    Args:
        order_id: The internal numeric order ID.
        reason: The customer's reason for cancellation.
    """
    # Fetch current order state
    rows = execute_query(
        "SELECT order_id, order_status, is_cancellable FROM orders WHERE order_id = %s",
        (order_id,),
    )
    if not rows:
        return {"error": f"No order found with order_id {order_id}."}

    order = rows[0]

    if not order["is_cancellable"]:
        return {
            "error": "This order is marked as non-cancellable. "
            "Please contact support for assistance."
        }

    if order["order_status"] not in _CANCELLABLE_STATUSES:
        return {
            "error": f"Order cannot be cancelled — current status is "
            f"'{order['order_status']}'. Cancellation is only allowed "
            f"when status is: {', '.join(sorted(_CANCELLABLE_STATUSES))}."
        }

    if not reason or len(reason.strip()) < 5:
        return {"error": "Please provide a meaningful cancellation reason (at least 5 characters)."}

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    affected = execute_update(
        """
        UPDATE orders
        SET order_status = 'cancelled',
            cancellation_reason = %s,
            cancelled_at = %s,
            is_cancellable = 0
        WHERE order_id = %s AND order_status IN ('pending','confirmed','processing')
        """,
        (reason.strip(), now, order_id),
    )

    if affected == 0:
        return {"error": "Cancellation failed — the order may have been updated concurrently."}

    return {
        "success": True,
        "message": f"Order {order_id} has been cancelled successfully.",
        "cancellation_reason": reason.strip(),
        "cancelled_at": now,
    }


@tool
def update_order_status(order_id: int, new_status: str) -> dict:
    """Update the status of an order following valid state-machine transitions.

    Only valid transitions are allowed:
      pending -> confirmed / cancelled / failed
      confirmed -> processing / cancelled
      processing -> shipped / cancelled
      shipped -> out_for_delivery
      out_for_delivery -> delivered / failed
      delivered -> return_requested
      return_requested -> returned

    Args:
        order_id: The internal numeric order ID.
        new_status: The target status to transition to.
    """
    rows = execute_query(
        "SELECT order_id, order_status FROM orders WHERE order_id = %s",
        (order_id,),
    )
    if not rows:
        return {"error": f"No order found with order_id {order_id}."}

    current_status = rows[0]["order_status"]
    allowed = _ORDER_TRANSITIONS.get(current_status, set())

    if new_status not in allowed:
        return {
            "error": f"Cannot transition from '{current_status}' to '{new_status}'. "
            f"Allowed transitions: {sorted(allowed) if allowed else 'none (terminal state)'}."
        }

    # Determine which timestamp column to update
    timestamp_col_map = {
        "confirmed": "confirmed_at",
        "shipped": "shipped_at",
        "delivered": "delivered_at",
        "cancelled": "cancelled_at",
    }
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    ts_col = timestamp_col_map.get(new_status)
    if ts_col:
        execute_update(
            f"UPDATE orders SET order_status = %s, {ts_col} = %s WHERE order_id = %s",
            (new_status, now, order_id),
        )
    else:
        execute_update(
            "UPDATE orders SET order_status = %s WHERE order_id = %s",
            (new_status, order_id),
        )

    return {
        "success": True,
        "message": f"Order {order_id} status updated from '{current_status}' to '{new_status}'.",
    }
