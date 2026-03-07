from datetime import datetime, timezone

from langchain_core.tools import tool

from src.db import execute_query, execute_update


@tool
def get_user_notifications(user_id: int, unread_only: bool = False) -> list:
    """Get notifications for a customer, most recent first.

    Returns notification type, title, message, channel, read status.
    Can be filtered to show only unread notifications. Limited to 30.

    Args:
        user_id: The customer's user ID.
        unread_only: If True, only return unread notifications.
    """
    if unread_only:
        rows = execute_query(
            """
            SELECT notification_id, type, title, message, channel,
                   is_read, sent_at
            FROM notifications
            WHERE user_id = %s AND is_read = 0
            ORDER BY sent_at DESC
            LIMIT 30
            """,
            (user_id,),
        )
    else:
        rows = execute_query(
            """
            SELECT notification_id, type, title, message, channel,
                   is_read, sent_at
            FROM notifications
            WHERE user_id = %s
            ORDER BY sent_at DESC
            LIMIT 30
            """,
            (user_id,),
        )

    if not rows:
        msg = "No unread notifications." if unread_only else "No notifications found."
        return {"message": msg}
    return rows


@tool
def mark_notification_read(notification_id: int) -> dict:
    """Mark a specific notification as read.

    Sets is_read = 1 and records the read_at timestamp.

    Args:
        notification_id: The notification identifier.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    affected = execute_update(
        "UPDATE notifications SET is_read = 1, read_at = %s WHERE notification_id = %s AND is_read = 0",
        (now, notification_id),
    )
    if affected == 0:
        return {"message": "Notification not found or already read."}
    return {"success": True, "message": "Notification marked as read."}
