from langchain_core.tools import tool

from src.db import execute_query, execute_insert, execute_update


@tool
def add_to_cart(user_id: int, product_id: int, quantity: int = 1) -> dict:
    """Add a product to the customer's shopping cart.

    Business rules enforced:
    - Product must be active and in stock.
    - Requested quantity must not exceed available stock.
    - If the product is already in the cart, the quantity is incremented.

    Args:
        user_id: The customer's user ID.
        product_id: The product to add.
        quantity: Number of units to add (default 1, must be >= 1).
    """
    if quantity < 1:
        return {"error": "Quantity must be at least 1."}

    # Check product availability
    product_rows = execute_query(
        "SELECT product_id, name, stock_quantity, is_active FROM products WHERE product_id = %s",
        (product_id,),
    )
    if not product_rows:
        return {"error": f"Product {product_id} not found."}

    product = product_rows[0]
    if not product["is_active"]:
        return {"error": f"'{product['name']}' is currently unavailable."}
    if product["stock_quantity"] < quantity:
        return {
            "error": f"Insufficient stock for '{product['name']}'. "
            f"Available: {product['stock_quantity']}, requested: {quantity}."
        }

    # Check if already in cart
    existing = execute_query(
        "SELECT cart_item_id, quantity FROM cart_items "
        "WHERE user_id = %s AND product_id = %s",
        (user_id, product_id),
    )

    if existing:
        new_qty = existing[0]["quantity"] + quantity
        if new_qty > product["stock_quantity"]:
            return {
                "error": f"Cannot add more — total would be {new_qty} but only "
                f"{product['stock_quantity']} available."
            }
        execute_update(
            "UPDATE cart_items SET quantity = %s WHERE cart_item_id = %s",
            (new_qty, existing[0]["cart_item_id"]),
        )
        return {
            "success": True,
            "message": f"Updated '{product['name']}' quantity to {new_qty} in your cart.",
        }

    # Add new cart item
    execute_insert(
        "INSERT INTO cart_items (user_id, product_id, quantity) VALUES (%s, %s, %s)",
        (user_id, product_id, quantity),
    )
    return {
        "success": True,
        "message": f"Added '{product['name']}' (x{quantity}) to your cart.",
    }


@tool
def update_cart_quantity(cart_item_id: int, quantity: int) -> dict:
    """Update the quantity of an item already in the cart.

    Validates that the new quantity does not exceed available stock.
    Set quantity to 0 to remove the item.

    Args:
        cart_item_id: The cart item identifier.
        quantity: The new quantity (0 to remove, must be non-negative).
    """
    if quantity < 0:
        return {"error": "Quantity cannot be negative."}

    if quantity == 0:
        execute_update(
            "DELETE FROM cart_items WHERE cart_item_id = %s",
            (cart_item_id,),
        )
        return {"success": True, "message": "Item removed from cart."}

    # Fetch current cart item and check stock
    rows = execute_query(
        """
        SELECT ci.cart_item_id, ci.product_id, p.stock_quantity, p.name, p.is_active
        FROM cart_items ci
        JOIN products p ON ci.product_id = p.product_id
        WHERE ci.cart_item_id = %s
        """,
        (cart_item_id,),
    )
    if not rows:
        return {"error": f"Cart item {cart_item_id} not found."}

    item = rows[0]
    if quantity > item["stock_quantity"]:
        return {
            "error": f"Cannot set quantity to {quantity} — only "
            f"{item['stock_quantity']} of '{item['name']}' available."
        }

    execute_update(
        "UPDATE cart_items SET quantity = %s WHERE cart_item_id = %s",
        (quantity, cart_item_id),
    )
    return {
        "success": True,
        "message": f"Updated '{item['name']}' quantity to {quantity}.",
    }


@tool
def remove_from_cart(cart_item_id: int) -> dict:
    """Remove an item from the customer's shopping cart.

    Args:
        cart_item_id: The cart item identifier to remove.
    """
    affected = execute_update(
        "DELETE FROM cart_items WHERE cart_item_id = %s",
        (cart_item_id,),
    )
    if affected == 0:
        return {"error": f"Cart item {cart_item_id} not found."}
    return {"success": True, "message": "Item removed from cart."}


@tool
def add_to_wishlist(user_id: int, product_id: int) -> dict:
    """Add a product to the customer's wishlist.

    Prevents duplicate entries — if the product is already wishlisted,
    returns a friendly message instead of creating a duplicate.

    Args:
        user_id: The customer's user ID.
        product_id: The product to add to the wishlist.
    """
    # Check product exists
    product_rows = execute_query(
        "SELECT product_id, name FROM products WHERE product_id = %s",
        (product_id,),
    )
    if not product_rows:
        return {"error": f"Product {product_id} not found."}

    # Check for duplicate
    existing = execute_query(
        "SELECT wishlist_id FROM wishlists WHERE user_id = %s AND product_id = %s",
        (user_id, product_id),
    )
    if existing:
        return {"message": f"'{product_rows[0]['name']}' is already in your wishlist."}

    execute_insert(
        "INSERT INTO wishlists (user_id, product_id) VALUES (%s, %s)",
        (user_id, product_id),
    )
    return {
        "success": True,
        "message": f"Added '{product_rows[0]['name']}' to your wishlist.",
    }


@tool
def remove_from_wishlist(wishlist_id: int) -> dict:
    """Remove an item from the customer's wishlist.

    Args:
        wishlist_id: The wishlist entry identifier to remove.
    """
    affected = execute_update(
        "DELETE FROM wishlists WHERE wishlist_id = %s",
        (wishlist_id,),
    )
    if affected == 0:
        return {"error": f"Wishlist item {wishlist_id} not found."}
    return {"success": True, "message": "Item removed from wishlist."}
