import random
import string
from datetime import datetime, timezone

from langchain_core.tools import tool

from src.db import execute_insert, execute_query, execute_update

_VALID_CATEGORIES = {
    "order_issue", "delivery_issue", "return_refund",
    "payment_issue", "product_complaint", "account_issue",
    "general_inquiry", "escalation",
}

_VALID_PRIORITIES = {"low", "medium", "high", "urgent"}

_TICKET_STATUS_TRANSITIONS = {
    "open": {"in_progress", "waiting_on_customer", "resolved", "closed"},
    "in_progress": {"waiting_on_customer", "resolved", "closed"},
    "waiting_on_customer": {"in_progress", "resolved", "closed"},
    "resolved": {"closed", "open"},  # can reopen
}


def _generate_ticket_number() -> str:
    """Generate a unique ticket number like TKT-XXXXXXXX."""
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"TKT-{suffix}"


@tool
def create_support_ticket(
    user_id: int,
    category: str,
    subject: str,
    description: str,
    order_id: int | None = None,
    priority: str = "medium",
) -> dict:
    """Create a new support ticket for a customer.

    Use this when the customer has an issue that cannot be resolved directly
    and needs to be escalated to the support team.

    Args:
        user_id: The customer's user ID.
        category: Ticket category — one of: order_issue, delivery_issue,
            return_refund, payment_issue, product_complaint, account_issue,
            general_inquiry, escalation.
        subject: Brief subject line for the ticket.
        description: Detailed description of the customer's issue.
        order_id: Optional associated order ID.
        priority: Ticket priority — low, medium (default), high, urgent.
    """
    if category not in _VALID_CATEGORIES:
        return {"error": f"Invalid category '{category}'. Valid: {sorted(_VALID_CATEGORIES)}"}

    if priority not in _VALID_PRIORITIES:
        return {"error": f"Invalid priority '{priority}'. Valid: {sorted(_VALID_PRIORITIES)}"}

    if not subject or len(subject.strip()) < 5:
        return {"error": "Subject must be at least 5 characters."}

    if not description or len(description.strip()) < 10:
        return {"error": "Description must be at least 10 characters."}

    # Verify user exists
    user_rows = execute_query(
        "SELECT user_id FROM users WHERE user_id = %s", (user_id,)
    )
    if not user_rows:
        return {"error": f"No user found with user_id {user_id}."}

    # Verify order if provided
    if order_id is not None:
        order_rows = execute_query(
            "SELECT order_id, user_id FROM orders WHERE order_id = %s",
            (order_id,),
        )
        if not order_rows:
            return {"error": f"No order found with order_id {order_id}."}
        if order_rows[0]["user_id"] != user_id:
            return {"error": "The specified order does not belong to this user."}

    ticket_number = _generate_ticket_number()

    ticket_id = execute_insert(
        """
        INSERT INTO support_tickets
            (ticket_number, user_id, order_id, category, subject,
             description, priority, status, source)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'open', 'diya_escalation')
        """,
        (
            ticket_number, user_id, order_id, category,
            subject.strip(), description.strip(), priority,
        ),
    )

    return {
        "success": True,
        "ticket_id": ticket_id,
        "ticket_number": ticket_number,
        "message": f"Support ticket {ticket_number} created successfully. "
        f"Our team will respond shortly.",
    }


@tool
def update_ticket_status(ticket_id: int, new_status: str) -> dict:
    """Update the status of a support ticket.

    Valid transitions:
      open -> in_progress / waiting_on_customer / resolved / closed
      in_progress -> waiting_on_customer / resolved / closed
      waiting_on_customer -> in_progress / resolved / closed
      resolved -> closed / open (reopen)

    Args:
        ticket_id: The ticket identifier.
        new_status: The target ticket status.
    """
    rows = execute_query(
        "SELECT ticket_id, status FROM support_tickets WHERE ticket_id = %s",
        (ticket_id,),
    )
    if not rows:
        return {"error": f"No ticket found with ticket_id {ticket_id}."}

    current = rows[0]["status"]
    allowed = _TICKET_STATUS_TRANSITIONS.get(current, set())

    if new_status not in allowed:
        return {
            "error": f"Cannot transition ticket from '{current}' to '{new_status}'. "
            f"Allowed: {sorted(allowed) if allowed else 'none (terminal state)'}."
        }

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    if new_status == "resolved":
        execute_update(
            "UPDATE support_tickets SET status = %s, resolved_at = %s WHERE ticket_id = %s",
            (new_status, now, ticket_id),
        )
    else:
        execute_update(
            "UPDATE support_tickets SET status = %s WHERE ticket_id = %s",
            (new_status, ticket_id),
        )

    return {
        "success": True,
        "message": f"Ticket {ticket_id} status updated from '{current}' to '{new_status}'.",
    }
