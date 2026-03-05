from typing import Any

from mysql.connector import pooling

from src.config import settings

_pool: pooling.MySQLConnectionPool | None = None


def _get_pool() -> pooling.MySQLConnectionPool:
    """Get or create the MySQL connection pool (singleton)."""
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="kvkart_pool",
            pool_size=5,
            pool_reset_session=True,
            host=settings.MYSQL_HOST,
            port=settings.MYSQL_PORT,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
            database=settings.MYSQL_DATABASE,
            autocommit=False,
        )
    return _pool


def execute_query(sql: str, params: tuple | dict | None = None) -> list[dict[str, Any]]:
    """
    Execute a SELECT query and return results as a list of dicts.

    Args:
        sql: The SQL SELECT statement to execute.
        params: Optional query parameters (tuple for %s placeholders,
                dict for %(name)s placeholders).

    Returns:
        List of dictionaries, one per row, with column names as keys.
    """
    pool = _get_pool()
    conn = pool.get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, params)
        results = cursor.fetchall()
        cursor.close()
        return results
    finally:
        conn.close()


def execute_update(sql: str, params: tuple | dict | None = None) -> int:
    """
    Execute an INSERT, UPDATE, or DELETE statement.

    Args:
        sql: The SQL modification statement to execute.
        params: Optional query parameters.

    Returns:
        The number of rows affected.
    """
    pool = _get_pool()
    conn = pool.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        affected = cursor.rowcount
        cursor.close()
        return affected
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def execute_insert(sql: str, params: tuple | dict | None = None) -> int:
    """
    Execute an INSERT statement and return the last inserted ID.

    Args:
        sql: The SQL INSERT statement to execute.
        params: Optional query parameters.

    Returns:
        The auto-generated ID of the inserted row.
    """
    pool = _get_pool()
    conn = pool.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        last_id = cursor.lastrowid
        cursor.close()
        return last_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
