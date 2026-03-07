from langchain_core.tools import tool

from src.db import execute_query


@tool
def get_product_by_id(product_id: int) -> dict:
    """Retrieve full product details including brand and category names.

    Returns product info with pricing, stock, ratings, and associated
    brand / category metadata.

    Args:
        product_id: The numeric product identifier.
    """
    rows = execute_query(
        """
        SELECT p.*, b.name AS brand_name, c.name AS category_name
        FROM products p
        LEFT JOIN brands b ON p.brand_id = b.brand_id
        LEFT JOIN categories c ON p.category_id = c.category_id
        WHERE p.product_id = %s
        """,
        (product_id,),
    )
    if not rows:
        return {"error": f"No product found with product_id {product_id}."}
    return rows[0]


@tool
def search_products(
    query: str,
    category_id: int | None = None,
    brand_id: int | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
) -> list:
    """Search the product catalog by keyword with optional filters.

    Searches product name, description, and tags. Results are limited to
    active products and sorted by average rating (best first). Max 20 results.

    Args:
        query: Search keyword(s) to match against product name, description, or tags.
        category_id: Optional category ID to restrict results.
        brand_id: Optional brand ID to restrict results.
        min_price: Optional minimum selling price filter.
        max_price: Optional maximum selling price filter.
    """
    conditions = ["p.is_active = 1"]
    params: list = []

    if query:
        conditions.append("(p.name LIKE %s OR p.description LIKE %s OR p.tags LIKE %s)")
        like_pattern = f"%{query}%"
        params.extend([like_pattern, like_pattern, like_pattern])

    if category_id is not None:
        conditions.append("p.category_id = %s")
        params.append(category_id)

    if brand_id is not None:
        conditions.append("p.brand_id = %s")
        params.append(brand_id)

    if min_price is not None:
        conditions.append("p.selling_price >= %s")
        params.append(min_price)

    if max_price is not None:
        conditions.append("p.selling_price <= %s")
        params.append(max_price)

    where_clause = " AND ".join(conditions)

    rows = execute_query(
        f"""
        SELECT p.product_id, p.name, p.selling_price, p.base_price,
               p.discount_percent, p.stock_quantity, p.average_rating,
               p.total_ratings, b.name AS brand_name, c.name AS category_name
        FROM products p
        LEFT JOIN brands b ON p.brand_id = b.brand_id
        LEFT JOIN categories c ON p.category_id = c.category_id
        WHERE {where_clause}
        ORDER BY p.average_rating DESC, p.total_ratings DESC
        LIMIT 20
        """,
        tuple(params),
    )
    if not rows:
        return {"message": "No products matched your search criteria."}
    return rows


@tool
def get_products_by_category(category_id: int) -> list:
    """Get all active products in a specific category.

    Useful when a customer wants to browse a category. Results sorted by
    popularity (rating). Limited to 30 products.

    Args:
        category_id: The category identifier to browse.
    """
    rows = execute_query(
        """
        SELECT p.product_id, p.name, p.selling_price, p.discount_percent,
               p.stock_quantity, p.average_rating, b.name AS brand_name
        FROM products p
        LEFT JOIN brands b ON p.brand_id = b.brand_id
        WHERE p.category_id = %s AND p.is_active = 1
        ORDER BY p.average_rating DESC
        LIMIT 30
        """,
        (category_id,),
    )
    if not rows:
        return {"message": f"No active products found in category {category_id}."}
    return rows


@tool
def get_products_by_brand(brand_id: int) -> list:
    """Get all active products from a specific brand.

    Useful when a customer asks about products from a particular brand.
    Results sorted by popularity. Limited to 30 products.

    Args:
        brand_id: The brand identifier.
    """
    rows = execute_query(
        """
        SELECT p.product_id, p.name, p.selling_price, p.discount_percent,
               p.stock_quantity, p.average_rating, c.name AS category_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.category_id
        WHERE p.brand_id = %s AND p.is_active = 1
        ORDER BY p.average_rating DESC
        LIMIT 30
        """,
        (brand_id,),
    )
    if not rows:
        return {"message": f"No active products found for brand {brand_id}."}
    return rows


@tool
def get_product_reviews(product_id: int) -> list:
    """Get customer reviews for a product, most helpful first.

    Returns verified purchase reviews with rating, title, body, and
    helpfulness count. Limited to 20 most helpful reviews.

    Args:
        product_id: The product to fetch reviews for.
    """
    rows = execute_query(
        """
        SELECT pr.review_id, pr.rating, pr.title, pr.body,
               pr.is_verified_purchase, pr.helpful_count, pr.created_at,
               u.first_name
        FROM product_reviews pr
        JOIN users u ON pr.user_id = u.user_id
        WHERE pr.product_id = %s
        ORDER BY pr.helpful_count DESC, pr.created_at DESC
        LIMIT 20
        """,
        (product_id,),
    )
    if not rows:
        return {"message": f"No reviews found for product {product_id}."}
    return rows


@tool
def get_all_categories() -> list:
    """List all active product categories with their hierarchy.

    Returns category ID, name, parent category, and description.
    Useful for helping customers navigate the catalog.
    """
    rows = execute_query(
        """
        SELECT c.category_id, c.name, c.description,
               pc.name AS parent_category_name
        FROM categories c
        LEFT JOIN categories pc ON c.parent_category_id = pc.category_id
        WHERE c.is_active = 1
        ORDER BY c.parent_category_id, c.name
        """
    )
    return rows


@tool
def get_all_brands() -> list:
    """List all active brands available on the platform.

    Returns brand ID, name, and logo URL. Useful when a customer asks
    'What brands do you carry?'
    """
    rows = execute_query(
        "SELECT brand_id, name, logo_url FROM brands WHERE is_active = 1 ORDER BY name"
    )
    return rows


@tool
def get_bulk_products_by_ids(product_ids: list[int]) -> list:
    """Retrieve multiple products at once by their IDs.

    Useful for displaying details of several products in a single call
    (e.g. items in a cart or wishlist). Limited to 30 IDs per call.

    Args:
        product_ids: A list of product IDs (max 30).
    """
    if not product_ids:
        return {"error": "product_ids list cannot be empty."}
    if len(product_ids) > 30:
        return {"error": "Cannot fetch more than 30 products at once."}

    placeholders = ",".join(["%s"] * len(product_ids))
    rows = execute_query(
        f"""
        SELECT p.*, b.name AS brand_name, c.name AS category_name
        FROM products p
        LEFT JOIN brands b ON p.brand_id = b.brand_id
        LEFT JOIN categories c ON p.category_id = c.category_id
        WHERE p.product_id IN ({placeholders})
        """,
        tuple(product_ids),
    )
    return rows


@tool
def check_product_availability(product_id: int) -> dict:
    """Check whether a product is in stock and available for purchase.

    Returns the stock quantity, active status, and a human-readable
    availability message. Useful before adding to cart.

    Args:
        product_id: The product to check availability for.
    """
    rows = execute_query(
        "SELECT product_id, name, stock_quantity, is_active FROM products WHERE product_id = %s",
        (product_id,),
    )
    if not rows:
        return {"error": f"No product found with product_id {product_id}."}

    product = rows[0]
    in_stock = product["is_active"] and product["stock_quantity"] > 0

    return {
        "product_id": product["product_id"],
        "product_name": product["name"],
        "is_active": bool(product["is_active"]),
        "stock_quantity": product["stock_quantity"],
        "available": in_stock,
        "message": (
            f"'{product['name']}' is available ({product['stock_quantity']} in stock)."
            if in_stock
            else f"'{product['name']}' is currently unavailable."
        ),
    }
