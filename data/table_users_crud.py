# table_users_crud.py
from datetime import datetime
from data.db_connection import get_connection

# -----------------------------
# INSERT FUNCTIONS
# -----------------------------

conn = get_connection()
if conn:
    with conn.cursor() as cur:
        cur.execute("SELECT NOW();")
        print("Supabase server time:", cur.fetchone())

def insert_users(username: str, email: str, user_ins: str):
    """Insert a single user into the users table."""
    try:
        conn = get_connection()
        if not conn:
            return
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users (username, email, user_ins, timestamp_ins)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (username, email, user_ins, datetime.now())
                )
        print(f"User '{username}' inserted successfully!")
    except Exception as e:
        print(f"Error inserting user '{username}': {e}")


def insert_users_ft(username: str, email: str):
    """Insert a first-time user into the users table."""
    try:
        conn = get_connection()
        if not conn:
            return
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users (username, email, timestamp_ins)
                    VALUES (%s, %s, %s)
                    """,
                    (username, email, datetime.now())
                )
        print(f"User '{username}' inserted successfully!")
    except Exception as e:
        print(f"Error inserting user '{username}': {e}")


# -----------------------------
# SELECT FUNCTIONS
# -----------------------------

def fetch_users_by_seq_no(seq_no: int):
    """Fetch a single user by seq_no."""
    try:
        conn = get_connection()
        if not conn:
            return None
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT username, email, user_ins, timestamp_ins, user_upd, timestamp_upd, seq_no
                FROM users
                WHERE seq_no = %s
                """,
                (seq_no,)
            )
            return cur.fetchone()
    except Exception as e:
        print(f"Error fetching user seq_no={seq_no}: {e}")
        return None


def fetch_all_users():
    """Fetch all users."""
    try:
        conn = get_connection()
        if not conn:
            return []
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT username, email, user_ins, timestamp_ins, user_upd, timestamp_upd, seq_no
                FROM users
                ORDER BY seq_no ASC
                """
            )
            return cur.fetchall()
    except Exception as e:
        print(f"Error fetching all users: {e}")
        return []


def fetch_user_seq_no(username: str, email: str):
    """Returns the seq_no of a user by username and email."""
    users = fetch_all_users()
    for user in users:
        if user["username"] == username and user["email"] == email:
            return user["seq_no"]
    return None


# -----------------------------
# UPDATE FUNCTION
# -----------------------------

def update_users(seq_no: int, updates: dict):
    """
    Update a user by seq_no.
    updates: dict with column names and new values
    """
    try:
        conn = get_connection()
        if not conn:
            return
        set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
        values = list(updates.values())
        values.append(datetime.now())  # timestamp_upd
        values.append(seq_no)          # WHERE seq_no
        query = f"UPDATE users SET {set_clause}, timestamp_upd = %s WHERE seq_no = %s"
        with conn:
            with conn.cursor() as cur:
                cur.execute(query, tuple(values))
        print(f"User seq_no={seq_no} updated successfully!")
    except Exception as e:
        print(f"Error updating user seq_no={seq_no}: {e}")


# -----------------------------
# DELETE FUNCTION
# -----------------------------

def delete_users(seq_no: int):
    """Delete a user by seq_no."""
    try:
        conn = get_connection()
        if not conn:
            return
        with conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM users WHERE seq_no = %s", (seq_no,))
        print(f"User seq_no={seq_no} deleted successfully!")
    except Exception as e:
        print(f"Error deleting user seq_no={seq_no}: {e}")
