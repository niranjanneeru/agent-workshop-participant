from langchain_core.tools import tool

from src.db import execute_query


def _mask_email(email: str) -> str:
    """Mask the middle portion of an email for privacy."""
    if not email or "@" not in email:
        return email
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = local[0] + "***"
    else:
        masked_local = local[0] + "***" + local[-1]
    return f"{masked_local}@{domain}"


def _mask_phone(phone: str) -> str:
    """Mask all but the last 4 digits of a phone number."""
    if not phone or len(phone) < 4:
        return phone
    return "X" * (len(phone) - 4) + phone[-4:]


@tool
def get_user_profile(user_id: int) -> dict:
    """Retrieve a customer's profile information.

    Returns name, masked email/phone, account status, premium membership
    details, and account creation date. Email and phone are partially masked
    for privacy.

    Args:
        user_id: The customer's user ID.
    """
    rows = execute_query(
        """
        SELECT user_id, first_name, last_name, email, phone,
               date_of_birth, gender, account_status,
               is_premium_member, premium_expiry, created_at, last_login_at
        FROM users WHERE user_id = %s
        """,
        (user_id,),
    )
    if not rows:
        return {"error": f"No user found with user_id {user_id}."}

    user = rows[0]
    user["email"] = _mask_email(user.get("email", ""))
    user["phone"] = _mask_phone(user.get("phone", ""))
    return user


@tool
def get_user_by_email(email: str) -> dict:
    """Look up a customer by their email address.

    Returns basic profile info with masked sensitive fields.
    Useful for identifying a customer at the start of a conversation.

    Args:
        email: The customer's email address.
    """
    rows = execute_query(
        """
        SELECT user_id, first_name, last_name, email, phone,
               account_status, is_premium_member
        FROM users WHERE email = %s
        """,
        (email,),
    )
    if not rows:
        return {"error": f"No user found with email '{email}'."}

    user = rows[0]
    user["email"] = _mask_email(user.get("email", ""))
    user["phone"] = _mask_phone(user.get("phone", ""))
    return user


@tool
def get_user_addresses(user_id: int) -> list:
    """Get all saved addresses for a customer.

    Returns address label (home/work/etc.), full address details,
    and which address is the default. Useful for order placement
    and delivery queries.

    Args:
        user_id: The customer's user ID.
    """
    rows = execute_query(
        """
        SELECT address_id, label, full_name, phone, address_line1,
               address_line2, city, state, pincode, country, is_default
        FROM addresses
        WHERE user_id = %s
        ORDER BY is_default DESC, created_at DESC
        """,
        (user_id,),
    )
    if not rows:
        return {"message": "No saved addresses found for this user."}
    return rows
