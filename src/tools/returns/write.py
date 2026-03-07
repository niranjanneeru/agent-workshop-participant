from datetime import datetime, timezone

from langchain_core.tools import tool

from src.db import execute_insert, execute_query, execute_update

# Maximum number of days after delivery that a return can be requested
_RETURN_WINDOW_DAYS = 7

_VALID_RETURN_REASONS = {
    "defective",
    "wrong_item",
    "not_as_described",
    "size_issue",
    "changed_mind",
    "arrived_late",
    "other",
}

_RETURN_STATUS_TRANSITIONS = {
    "requested": {"approved", "rejected"},
    "approved": {"pickup_scheduled"},
    "pickup_scheduled": {"picked_up"},
    "picked_up": {"received_at_warehouse"},
    "received_at_warehouse": {"inspected"},
    "inspected": {"refund_initiated", "rejected"},
    "refund_initiated": {"refund_completed"},
}


@tool
def create_return_request(
    order_id: int,
    order_item_id: int,
    user_id: int,
    reason: str,
    reason_detail: str = "",
) -> dict:
    """Create a return request for a delivered order item.

    Business rules enforced:
    - The order must belong to the given user.
    - The order status must be 'delivered'.
    - The return must be within the 7-day return window from delivery date.
    - The order item must be 'active' (not already cancelled/returned).
    - The reason must be one of: defective, wrong_item, not_as_described,
      size_issue, changed_mind, arrived_late, other.

    Args:
        order_id: The internal order ID.
        order_item_id: The specific order item to return.
        user_id: The customer's user ID (for ownership verification).
        reason: Return reason category.
        reason_detail: Optional free-text explanation.
    """
    # Validate reason
    if reason not in _VALID_RETURN_REASONS:
        return {
            "error": f"Invalid reason '{reason}'. Valid reasons: {sorted(_VALID_RETURN_REASONS)}"
        }

    # Verify order belongs to user and is delivered
    order_rows = execute_query(
        "SELECT order_id, user_id, order_status, delivered_at FROM orders WHERE order_id = %s",
        (order_id,),
    )
    if not order_rows:
        return {"error": f"No order found with order_id {order_id}."}

    order = order_rows[0]
    if order["user_id"] != user_id:
        return {"error": "This order does not belong to the specified user."}

    if order["order_status"] != "delivered":
        return {
            "error": f"Returns are only accepted for delivered orders. "
            f"Current status: '{order['order_status']}'."
        }

    # Check return window
    if order["delivered_at"]:
        delivered_dt = order["delivered_at"]
        if isinstance(delivered_dt, str):
            delivered_dt = datetime.fromisoformat(delivered_dt)
        now = datetime.now(timezone.utc)
        if delivered_dt.tzinfo is None:
            delivered_dt = delivered_dt.replace(tzinfo=timezone.utc)
        days_since = (now - delivered_dt).days
        if days_since > _RETURN_WINDOW_DAYS:
            return {
                "error": f"Return window expired. The order was delivered {days_since} "
                f"days ago. Returns are accepted within {_RETURN_WINDOW_DAYS} days."
            }

    # Verify the item exists and is active
    item_rows = execute_query(
        "SELECT order_item_id, item_status FROM order_items "
        "WHERE order_item_id = %s AND order_id = %s",
        (order_item_id, order_id),
    )
    if not item_rows:
        return {"error": f"Order item {order_item_id} not found in order {order_id}."}

    if item_rows[0]["item_status"] != "active":
        return {"error": f"This item has already been {item_rows[0]['item_status']}."}

    # Check for existing return request on this item
    existing = execute_query(
        "SELECT return_id FROM return_requests "
        "WHERE order_item_id = %s AND return_status NOT IN ('rejected')",
        (order_item_id,),
    )
    if existing:
        return {"error": "A return request already exists for this item."}

    # Create the return request
    return_id = execute_insert(
        """
        INSERT INTO return_requests
            (order_id, order_item_id, user_id, reason, reason_detail, return_status)
        VALUES (%s, %s, %s, %s, %s, 'requested')
        """,
        (order_id, order_item_id, user_id, reason, reason_detail or None),
    )

    return {
        "success": True,
        "return_id": return_id,
        "message": f"Return request created successfully (return_id: {return_id}). "
        f"Our team will review it shortly.",
    }


@tool
def update_return_status(return_id: int, new_status: str) -> dict:
    """Update the status of a return request following valid transitions.

    Valid transitions:
      requested -> approved / rejected
      approved -> pickup_scheduled
      pickup_scheduled -> picked_up
      picked_up -> received_at_warehouse
      received_at_warehouse -> inspected
      inspected -> refund_initiated / rejected
      refund_initiated -> refund_completed

    Args:
        return_id: The return request identifier.
        new_status: The target return status.
    """
    rows = execute_query(
        "SELECT return_id, return_status FROM return_requests WHERE return_id = %s",
        (return_id,),
    )
    if not rows:
        return {"error": f"No return request found with return_id {return_id}."}

    current = rows[0]["return_status"]
    allowed = _RETURN_STATUS_TRANSITIONS.get(current, set())

    if new_status not in allowed:
        return {
            "error": f"Cannot transition return from '{current}' to '{new_status}'. "
            f"Allowed: {sorted(allowed) if allowed else 'none (terminal state)'}."
        }

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # If resolved (completed or rejected), set resolved_at
    if new_status in ("refund_completed", "rejected"):
        execute_update(
            "UPDATE return_requests SET return_status = %s, resolved_at = %s WHERE return_id = %s",
            (new_status, now, return_id),
        )
    else:
        execute_update(
            "UPDATE return_requests SET return_status = %s WHERE return_id = %s",
            (new_status, return_id),
        )

    return {
        "success": True,
        "message": f"Return {return_id} status updated from '{current}' to '{new_status}'.",
    }
