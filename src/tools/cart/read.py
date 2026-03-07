from langchain_core.tools import tool

from src.db import execute_query


@tool
def get_cart_items(user_id: int) -> dict:
    """Get all items in a customer's shopping cart with product details.

    Returns each cart item with product name, price, stock status, and
    the computed cart total. Useful for reviewing the cart before checkout.

    Args:
        user_id: The customer's user ID.
    """
    rows = execute_query(
        """
        SELECT ci.cart_item_id, ci.product_id, ci.quantity, ci.added_at,
               p.name AS product_name, p.selling_price, p.stock_quantity,
               p.is_active,
               (ci.quantity * p.selling_price) AS line_total
        FROM cart_items ci
        JOIN products p ON ci.product_id = p.product_id
        WHERE ci.user_id = %s
        ORDER BY ci.added_at DESC
        """,
        (user_id,),
    )
    if not rows:
        return {"message": "Your cart is empty.", "items": [], "cart_total": 0}

    cart_total = sum(float(row["line_total"]) for row in rows)
    return {
        "items": rows,
        "cart_total": round(cart_total, 2),
        "item_count": len(rows),
    }


@tool
def get_wishlist(user_id: int) -> list:
    """Get all items in a customer's wishlist with product details.

    Returns product name, price, availability, and when it was added.
    Useful when a customer wants to review saved items.

    Args:
        user_id: The customer's user ID.
    """
    rows = execute_query(
        """
        SELECT w.wishlist_id, w.product_id, w.added_at,
               p.name AS product_name, p.selling_price,
               p.stock_quantity, p.is_active,
               p.discount_percent
        FROM wishlists w
        JOIN products p ON w.product_id = p.product_id
        WHERE w.user_id = %s
        ORDER BY w.added_at DESC
        """,
        (user_id,),
    )
    if not rows:
        return {"message": "Your wishlist is empty."}
    return rows
