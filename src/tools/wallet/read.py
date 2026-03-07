from langchain_core.tools import tool

from src.db import execute_query


@tool
def get_wallet_balance(user_id: int) -> dict:
    """Get the current wallet balance for a customer.

    Returns the balance amount and last updated timestamp.
    Useful when a customer asks 'How much is in my wallet?'

    Args:
        user_id: The customer's user ID.
    """
    rows = execute_query(
        "SELECT wallet_id, user_id, balance, last_updated_at FROM wallet WHERE user_id = %s",
        (user_id,),
    )
    if not rows:
        return {
            "message": "No wallet found for this user.",
            "balance": 0.00,
        }

    wallet = rows[0]
    return {
        "wallet_id": wallet["wallet_id"],
        "balance": float(wallet["balance"]),
        "last_updated_at": wallet["last_updated_at"],
        "message": f"Your wallet balance is ₹{float(wallet['balance']):.2f}.",
    }


@tool
def get_wallet_transactions(user_id: int, limit: int = 20) -> list:
    """Get recent wallet transactions for a customer.

    Returns transaction type (credit/debit), amount, description,
    reference type, and timestamp. Sorted most recent first.

    Args:
        user_id: The customer's user ID.
        limit: Maximum number of transactions to return (default 20, max 50).
    """
    if limit is None or limit < 1:
        limit = 20
    if limit > 50:
        limit = 50

    # First get the wallet_id for this user
    wallet_rows = execute_query(
        "SELECT wallet_id FROM wallet WHERE user_id = %s",
        (user_id,),
    )
    if not wallet_rows:
        return {"message": "No wallet found for this user."}

    wallet_id = wallet_rows[0]["wallet_id"]

    rows = execute_query(
        """
        SELECT txn_id, txn_type, amount, description,
               reference_type, reference_id, created_at
        FROM wallet_transactions
        WHERE wallet_id = %s
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (wallet_id, limit),
    )
    if not rows:
        return {"message": "No wallet transactions found."}
    return rows
