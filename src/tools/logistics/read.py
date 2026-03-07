from langchain_core.tools import tool

from src.db import execute_query


@tool
def get_shipment_by_order(order_id: int) -> dict:
    """Get shipment details for an order, including logistics partner name.

    Returns AWB number, shipment status, origin/destination cities,
    estimated and actual delivery dates, and last known location.

    Args:
        order_id: The internal order ID to look up the shipment for.
    """
    rows = execute_query(
        """
        SELECT s.*, lp.name AS logistics_partner_name,
               lp.tracking_url_template
        FROM shipments s
        JOIN logistics_partners lp ON s.logistics_partner_id = lp.partner_id
        WHERE s.order_id = %s
        """,
        (order_id,),
    )
    if not rows:
        return {"message": f"No shipment found for order_id {order_id}. The order may not have been shipped yet."}
    return rows[0]


@tool
def get_tracking_events(shipment_id: int) -> list:
    """Get all tracking events for a shipment in chronological order.

    Each event includes status, location, description, and timestamp.
    Useful for showing a step-by-step tracking timeline.

    Args:
        shipment_id: The shipment identifier.
    """
    rows = execute_query(
        """
        SELECT event_id, event_status, location, description, event_timestamp
        FROM shipment_tracking_events
        WHERE shipment_id = %s
        ORDER BY event_timestamp ASC
        """,
        (shipment_id,),
    )
    if not rows:
        return {"message": f"No tracking events found for shipment {shipment_id}."}
    return rows


@tool
def get_full_tracking_by_order(order_id: int) -> dict:
    """Get complete shipment info and all tracking events for an order.

    Combines shipment details with the full tracking timeline in one call.
    Best used when a customer asks 'Where is my order?'

    Args:
        order_id: The internal order ID.
    """
    # Fetch shipment
    shipment_rows = execute_query(
        """
        SELECT s.*, lp.name AS logistics_partner_name,
               lp.tracking_url_template
        FROM shipments s
        JOIN logistics_partners lp ON s.logistics_partner_id = lp.partner_id
        WHERE s.order_id = %s
        """,
        (order_id,),
    )
    if not shipment_rows:
        return {"message": f"No shipment found for order_id {order_id}."}

    shipment = shipment_rows[0]

    # Fetch tracking events
    events = execute_query(
        """
        SELECT event_status, location, description, event_timestamp
        FROM shipment_tracking_events
        WHERE shipment_id = %s
        ORDER BY event_timestamp ASC
        """,
        (shipment["shipment_id"],),
    )

    return {
        "shipment": shipment,
        "tracking_events": events,
    }


@tool
def get_delivery_estimate(origin_pincode: str, destination_pincode: str) -> list:
    """Estimate delivery time between two pincodes.

    Returns available logistics partners and their estimated delivery
    windows (min/max days) for the given route. Only serviceable routes
    are returned.

    Args:
        origin_pincode: The origin/warehouse pincode.
        destination_pincode: The customer's delivery pincode.
    """
    rows = execute_query(
        """
        SELECT de.estimated_days_min, de.estimated_days_max,
               de.is_serviceable, lp.name AS logistics_partner_name,
               lp.avg_delivery_days
        FROM delivery_estimates de
        JOIN logistics_partners lp ON de.logistics_partner_id = lp.partner_id
        WHERE de.origin_pincode = %s
          AND de.destination_pincode = %s
          AND de.is_serviceable = 1
          AND lp.is_active = 1
        """,
        (origin_pincode, destination_pincode),
    )
    if not rows:
        return {
            "message": f"No serviceable delivery route found from {origin_pincode} "
            f"to {destination_pincode}."
        }
    return rows


@tool
def get_logistics_partners() -> list:
    """List all active logistics / delivery partners.

    Returns partner name, average delivery days, and tracking URL template.
    """
    rows = execute_query(
        """
        SELECT partner_id, name, tracking_url_template, avg_delivery_days
        FROM logistics_partners
        WHERE is_active = 1
        ORDER BY name
        """
    )
    return rows


@tool
def get_bulk_shipments_by_orders(order_ids: list[int]) -> list:
    """Retrieve shipment details for multiple orders at once.

    Useful for getting tracking info for all of a customer's recent orders.
    Limited to 20 order IDs per call.

    Args:
        order_ids: List of order IDs (max 20).
    """
    if not order_ids:
        return {"error": "order_ids list cannot be empty."}
    if len(order_ids) > 20:
        return {"error": "Cannot fetch more than 20 shipments at once."}

    placeholders = ",".join(["%s"] * len(order_ids))
    rows = execute_query(
        f"""
        SELECT s.*, lp.name AS logistics_partner_name
        FROM shipments s
        JOIN logistics_partners lp ON s.logistics_partner_id = lp.partner_id
        WHERE s.order_id IN ({placeholders})
        ORDER BY s.created_at DESC
        """,
        tuple(order_ids),
    )
    return rows
