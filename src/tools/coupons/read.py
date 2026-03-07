from datetime import datetime, timezone

from langchain_core.tools import tool

from src.db import execute_query


@tool
def validate_coupon(code: str, user_id: int, order_amount: float) -> dict:
    """Validate whether a coupon code can be applied to an order.

    Performs comprehensive checks:
    - Coupon exists and is active.
    - Current date is within the valid_from / valid_until window.
    - Order amount meets the minimum order requirement.
    - Total usage limit has not been exceeded.
    - Per-user usage limit has not been exceeded.
    - User type eligibility (all / new / premium).

    If valid, returns the calculated discount amount.

    Args:
        code: The coupon code to validate.
        user_id: The customer's user ID.
        order_amount: The cart/order subtotal before discount.
    """
    # Fetch coupon
    coupon_rows = execute_query(
        "SELECT * FROM coupons WHERE code = %s",
        (code.upper(),),
    )
    if not coupon_rows:
        return {"valid": False, "error": f"Coupon code '{code}' not found."}

    coupon = coupon_rows[0]

    # Check active
    if not coupon["is_active"]:
        return {"valid": False, "error": "This coupon is no longer active."}

    # Check date validity
    now = datetime.now(timezone.utc)
    valid_from = coupon["valid_from"]
    valid_until = coupon["valid_until"]
    if isinstance(valid_from, str):
        valid_from = datetime.fromisoformat(valid_from)
    if isinstance(valid_until, str):
        valid_until = datetime.fromisoformat(valid_until)

    # Make naive datetimes UTC-aware for comparison
    if valid_from.tzinfo is None:
        valid_from = valid_from.replace(tzinfo=timezone.utc)
    if valid_until.tzinfo is None:
        valid_until = valid_until.replace(tzinfo=timezone.utc)

    if now < valid_from:
        return {"valid": False, "error": "This coupon is not yet active."}
    if now > valid_until:
        return {"valid": False, "error": "This coupon has expired."}

    # Check minimum order amount
    min_amount = float(coupon.get("min_order_amount") or 0)
    if order_amount < min_amount:
        return {
            "valid": False,
            "error": f"Minimum order amount is ₹{min_amount:.2f}. "
            f"Your order is ₹{order_amount:.2f}.",
        }

    # Check total usage limit
    if coupon["usage_limit_total"] is not None:
        if coupon["times_used"] >= coupon["usage_limit_total"]:
            return {
                "valid": False,
                "error": "This coupon has reached its maximum usage limit.",
            }

    # Check per-user usage limit
    if coupon["usage_limit_per_user"] is not None:
        user_usage = execute_query(
            "SELECT COUNT(*) AS cnt FROM coupon_usage WHERE coupon_id = %s AND user_id = %s",
            (coupon["coupon_id"], user_id),
        )
        if user_usage[0]["cnt"] >= coupon["usage_limit_per_user"]:
            return {
                "valid": False,
                "error": "You have already used this coupon the maximum number of times.",
            }

    # Check user type eligibility
    applicable_type = coupon.get("applicable_user_type", "all")
    if applicable_type != "all":
        user_rows = execute_query(
            "SELECT is_premium_member, created_at FROM users WHERE user_id = %s",
            (user_id,),
        )
        if not user_rows:
            return {"valid": False, "error": "User not found."}

        user = user_rows[0]
        if applicable_type == "premium" and not user["is_premium_member"]:
            return {
                "valid": False,
                "error": "This coupon is only available to premium members.",
            }
        if applicable_type == "new":
            # Consider users created within the last 30 days as "new"
            created = user["created_at"]
            if isinstance(created, str):
                created = datetime.fromisoformat(created)
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            days_since = (now - created).days
            if days_since > 30:
                return {
                    "valid": False,
                    "error": "This coupon is only for new customers (within 30 days of signup).",
                }

    # Calculate discount
    if coupon["discount_type"] == "percentage":
        discount = order_amount * float(coupon["discount_value"]) / 100.0
        max_disc = (
            float(coupon["max_discount_amount"])
            if coupon.get("max_discount_amount")
            else None
        )
        if max_disc and discount > max_disc:
            discount = max_disc
    else:  # flat
        discount = float(coupon["discount_value"])
        if discount > order_amount:
            discount = order_amount

    return {
        "valid": True,
        "coupon_code": coupon["code"],
        "discount_type": coupon["discount_type"],
        "discount_value": float(coupon["discount_value"]),
        "calculated_discount": round(discount, 2),
        "final_amount": round(order_amount - discount, 2),
        "message": f"Coupon '{coupon['code']}' applied! You save ₹{discount:.2f}.",
    }


@tool
def get_available_coupons(user_id: int | None = None) -> list:
    """List all currently valid and active coupons.

    Returns coupon code, description, discount details, and eligibility info.
    If user_id is provided, filters out coupons the user is not eligible for
    (based on user type).

    Args:
        user_id: Optional customer user ID to filter by eligibility.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    rows = execute_query(
        """
        SELECT coupon_id, code, description, discount_type, discount_value,
               min_order_amount, max_discount_amount, applicable_user_type,
               applicable_categories, valid_from, valid_until,
               usage_limit_total, times_used
        FROM coupons
        WHERE is_active = 1
          AND valid_from <= %s
          AND valid_until >= %s
          AND (usage_limit_total IS NULL OR times_used < usage_limit_total)
        ORDER BY discount_value DESC
        """,
        (now, now),
    )

    if not rows:
        return {"message": "No coupons are currently available."}

    # If user_id provided, filter by user type eligibility
    if user_id is not None:
        user_rows = execute_query(
            "SELECT is_premium_member, created_at FROM users WHERE user_id = %s",
            (user_id,),
        )
        if user_rows:
            user = user_rows[0]
            is_premium = user["is_premium_member"]
            created = user["created_at"]
            if isinstance(created, str):
                created = datetime.fromisoformat(created)
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            now_dt = datetime.now(timezone.utc)
            is_new = (now_dt - created).days <= 30

            filtered = []
            for c in rows:
                atype = c.get("applicable_user_type", "all")
                if atype == "all":
                    filtered.append(c)
                elif atype == "premium" and is_premium:
                    filtered.append(c)
                elif atype == "new" and is_new:
                    filtered.append(c)
            rows = filtered

    return rows
