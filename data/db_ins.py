from datetime import datetime
from data.db_connection import get_connection  # <- your existing file

def log_price(symbol: str, price: float):
    """
    Log a single asset price into the PostgreSQL `price_history` table.

    Args:
        symbol (str): The asset symbol (e.g., 'bitcoin', 'AAPL').
        price (float): The price to log.

    Notes:
        - Uses the current timestamp for the entry.
        - Caller must have a valid PostgreSQL database and table set up.
        - Errors are caught and printed; connection is closed automatically.
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO price_history (timestamp, symbol, price) VALUES (%s, %s, %s)",
            (datetime.now(), symbol, price)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error logging price: {e}")


def log_prices(prices: list):
    """
    Log multiple asset prices into the PostgreSQL `price_history` table in batch.

    Args:
        prices (list of tuple): List of tuples in the format (symbol, price).

    Notes:
        - Uses the current timestamp for all entries.
        - Errors are caught and printed; connection is closed automatically.
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        for symbol, price in prices:
            cur.execute(
                "INSERT INTO price_history (timestamp, symbol, price) VALUES (%s, %s, %s)",
                (datetime.now(), symbol, price)
            )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error logging prices: {e}")


def fetch_history(symbol: str):
    """
    Fetch historical price data for a given asset from the PostgreSQL `price_history` table.

    Args:
        symbol (str): The asset symbol (e.g., 'bitcoin', 'AAPL').

    Returns:
        list of tuples: Each tuple contains (timestamp, price), ordered ascending by timestamp.
        Returns an empty list if no data is found or an error occurs.

    Notes:
        - Caller is responsible for providing a valid symbol.
        - Errors are caught and printed; connection is closed automatically.
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT timestamp, price FROM price_history WHERE symbol=%s ORDER BY timestamp ASC",
            (symbol,)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        print(f"Error fetching history: {e}")
        return []
