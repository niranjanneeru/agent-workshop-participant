from langchain_core.tools import tool

from src.db import execute_query


@tool
def get_tickets_by_user(user_id: int) -> list:
    """Get all support tickets for a customer, most recent first.

    Returns ticket number, category, subject, priority, status, and timestamps.
    Includes the associated order number if applicable. Limited to 30 tickets.

    Args:
        user_id: The customer's user ID.
    """
    rows = execute_query(
        """
        SELECT st.ticket_id, st.ticket_number, st.category, st.subject,
               st.priority, st.status, st.source, st.created_at, st.updated_at,
               o.order_number
        FROM support_tickets st
        LEFT JOIN orders o ON st.order_id = o.order_id
        WHERE st.user_id = %s
        ORDER BY st.created_at DESC
        LIMIT 30
        """,
        (user_id,),
    )
    if not rows:
        return {"message": "No support tickets found for this user."}
    return rows


@tool
def get_ticket_details(ticket_id: int) -> dict:
    """Get full details of a specific support ticket.

    Returns all ticket fields including description, assigned agent,
    and resolution timestamp.

    Args:
        ticket_id: The ticket identifier.
    """
    rows = execute_query(
        """
        SELECT st.*, o.order_number
        FROM support_tickets st
        LEFT JOIN orders o ON st.order_id = o.order_id
        WHERE st.ticket_id = %s
        """,
        (ticket_id,),
    )
    if not rows:
        return {"error": f"No ticket found with ticket_id {ticket_id}."}
    return rows[0]
