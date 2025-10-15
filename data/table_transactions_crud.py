# table_transactions_crud.py
from datetime import datetime
from data.db_connection import get_connection

# -----------------------------
# INSERT FUNCTIONS
# -----------------------------

def insert_transaction(portfolio_seq_no: int, in_out: int, user_seq_no: int, asset_type: str, asset_code: str,
                       quantity: float, price: float, currency: str, user_ins: str):
    """Insert a single transaction record."""
    try:
        conn = get_connection()
        if not conn:
            return
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO transactions
                    (portfolio_seq_no, in_out, user_seq_no, asset_type, asset_code,
                     quantity, price, currency, timestamp_txn, user_ins, timestamp_ins)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (portfolio_seq_no, in_out, user_seq_no, asset_type, asset_code,
                     quantity, price, currency, datetime.now(), user_ins, datetime.now())
                )
        print("Transaction inserted successfully!")
    except Exception as e:
        print(f"Error inserting transaction: {e}")


def insert_transactions_batch(records: list):
    """Insert multiple transaction records at once."""
    try:
        conn = get_connection()
        if not conn:
            return
        with conn:
            with conn.cursor() as cur:
                for rec in records:
                    cur.execute(
                        """
                        INSERT INTO transactions
                        (portfolio_seq_no, in_out, user_seq_no, asset_type, asset_code,
                         quantity, price, currency, timestamp_txn, user_ins)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            rec["portfolio_seq_no"],
                            rec["in_out"],
                            rec["user_seq_no"],
                            rec["asset_type"],
                            rec["asset_code"],
                            rec["quantity"],
                            rec["price"],
                            rec["currency"],
                            datetime.now(),
                            rec["user_ins"]
                        )
                    )
        print(f"{len(records)} transactions inserted successfully!")
    except Exception as e:
        print(f"Error inserting transactions batch: {e}")


# -----------------------------
# SELECT FUNCTIONS
# -----------------------------

def fetch_transactions_by_seq_no(seq_no: int):
    """Fetch a single transaction by seq_no."""
    try:
        conn = get_connection()
        if not conn:
            return None
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT portfolio_seq_no, in_out, user_seq_no, asset_type, asset_code,
                       quantity, price, currency, timestamp_txn, user_ins, timestamp_ins,
                       user_upd, timestamp_upd, seq_no
                FROM transactions
                WHERE seq_no = %s
                """,
                (seq_no,)
            )
            return cur.fetchone()
    except Exception as e:
        print(f"Error fetching transaction seq_no={seq_no}: {e}")
        return None


def fetch_transactions_by_user_asset(asset_code: str, user_seq_no: int):
    """Fetch all transactions for a user and a specific asset."""
    try:
        conn = get_connection()
        print(f"conn={conn}")
        if not conn:
            return []
        with conn.cursor() as cur:
            print(f"conn={conn}")
           
            cur.execute(
                """
                SELECT portfolio_seq_no, in_out, user_seq_no, asset_type, asset_code,
                       quantity, price, currency, timestamp_txn, user_ins, timestamp_ins,
                       user_upd, timestamp_upd, seq_no
                FROM transactions
                WHERE asset_code = %s 
                AND user_seq_no  = %s
                """,
                (asset_code, user_seq_no,)
            )
            
            rows = cur.fetchall()
            print(f"cur.fetchall()={cur.fetchall()}")
            return rows
    except Exception as e:
        print(f"Error fetching transactions for user_seq_no={user_seq_no} and asset_code={asset_code}: {e}")
        return []


def fetch_all_user_transactions(user_seq_no: int):
    """Fetch all transactions for a specific user."""
    try:
        conn = get_connection()
        if not conn:
            return []
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT portfolio_seq_no, in_out, user_seq_no, asset_type, asset_code,
                       quantity, price, currency, timestamp_txn, user_ins, timestamp_ins,
                       user_upd, timestamp_upd, seq_no
                FROM transactions
                WHERE user_seq_no = %s
                ORDER BY timestamp_txn ASC
                """,
                (user_seq_no,)
            )
            return cur.fetchall()
    except Exception as e:
        print(f"Error fetching transactions for user_seq_no={user_seq_no}: {e}")
        return []


def fetch_all_transactions():
    """Fetch all transactions."""
    try:
        conn = get_connection()
        if not conn:
            return []
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT portfolio_seq_no, in_out, user_seq_no, asset_type, asset_code,
                       quantity, price, currency, timestamp_txn, user_ins, timestamp_ins,
                       user_upd, timestamp_upd, seq_no
                FROM transactions
                ORDER BY timestamp_txn ASC
                """
            )
            return cur.fetchall()
    except Exception as e:
        print(f"Error fetching all transactions: {e}")
        return []


# -----------------------------
# UPDATE FUNCTION
# -----------------------------

def update_transaction(seq_no: int, updates: dict):
    """Update a transaction by seq_no."""
    try:
        conn = get_connection()
        if not conn:
            return
        set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
        values = list(updates.values())
        values.append(datetime.now())  # timestamp_upd
        values.append(seq_no)          # WHERE seq_no
        query = f"UPDATE transactions SET {set_clause}, timestamp_upd = %s WHERE seq_no = %s"
        with conn:
            with conn.cursor() as cur:
                cur.execute(query, tuple(values))
        print(f"Transaction seq_no={seq_no} updated successfully!")
    except Exception as e:
        print(f"Error updating transaction seq_no={seq_no}: {e}")


# -----------------------------
# DELETE FUNCTION
# -----------------------------

def delete_transaction(seq_no: int):
    """Delete a transaction by seq_no."""
    try:
        conn = get_connection()
        if not conn:
            return
        with conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM transactions WHERE seq_no = %s", (seq_no,))
        print(f"Transaction seq_no={seq_no} deleted successfully!")
    except Exception as e:
        print(f"Error deleting transaction seq_no={seq_no}: {e}")
