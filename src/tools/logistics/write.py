from datetime import datetime, timezone

from langchain_core.tools import tool

from src.db import execute_query, execute_update

# Valid shipment status transitions
_SHIPMENT_TRANSITIONS = {
    "label_created": {"picked_up"},
    "picked_up": {"in_transit"},
    "in_transit": {"at_hub", "out_for_delivery"},
    "at_hub": {"in_transit", "out_for_delivery"},
    "out_for_delivery": {"delivered", "failed_attempt"},
    "failed_attempt": {"out_for_delivery", "returned_to_origin"},
}


@tool
def update_shipment_status(
    shipment_id: int,
    new_status: str,
    location: str | None = None,
) -> dict:
    """Update the status of a shipment with state-machine validation.

    Valid transitions:
      label_created -> picked_up
      picked_up -> in_transit
      in_transit -> at_hub / out_for_delivery
      at_hub -> in_transit / out_for_delivery
      out_for_delivery -> delivered / failed_attempt
      failed_attempt -> out_for_delivery / returned_to_origin

    Also inserts a tracking event and updates last_location if provided.

    Args:
        shipment_id: The shipment identifier.
        new_status: The target shipment status.
        location: Optional current location description.
    """
    rows = execute_query(
        "SELECT shipment_id, shipment_status FROM shipments WHERE shipment_id = %s",
        (shipment_id,),
    )
    if not rows:
        return {"error": f"No shipment found with shipment_id {shipment_id}."}

    current_status = rows[0]["shipment_status"]
    allowed = _SHIPMENT_TRANSITIONS.get(current_status, set())

    if new_status not in allowed:
        return {
            "error": f"Cannot transition shipment from '{current_status}' to '{new_status}'. "
            f"Allowed: {sorted(allowed) if allowed else 'none (terminal state)'}."
        }

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # Update shipment record
    if location:
        execute_update(
            """
            UPDATE shipments
            SET shipment_status = %s, last_location = %s, last_updated_at = %s
            WHERE shipment_id = %s
            """,
            (new_status, location, now, shipment_id),
        )
    else:
        execute_update(
            """
            UPDATE shipments
            SET shipment_status = %s, last_updated_at = %s
            WHERE shipment_id = %s
            """,
            (new_status, now, shipment_id),
        )

    # If delivered, also set actual_delivery_date
    if new_status == "delivered":
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        execute_update(
            "UPDATE shipments SET actual_delivery_date = %s WHERE shipment_id = %s",
            (today, shipment_id),
        )

    # Insert tracking event
    execute_update(
        """
        INSERT INTO shipment_tracking_events
            (shipment_id, event_status, location, description, event_timestamp)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            shipment_id,
            new_status,
            location or "N/A",
            f"Status updated to {new_status}",
            now,
        ),
    )

    return {
        "success": True,
        "message": f"Shipment {shipment_id} updated from '{current_status}' to '{new_status}'.",
    }
