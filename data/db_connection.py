# ==========================================================
# db_connection.py
# ==========================================================
# Handles PostgreSQL connections for both local Docker and Supabase.
# Uses environment variables and automatically applies SSL for Supabase.
# ==========================================================
import psycopg2
import os
from psycopg2.extras import RealDictCursor
import socket

# ==============================
# Force IPv4 for psycopg2
# ==============================
_original_getaddrinfo = socket.getaddrinfo
def getaddrinfo_ipv4_only(*args, **kwargs):
    results = _original_getaddrinfo(*args, **kwargs)
    # Only keep IPv4 addresses
    return [x for x in results if x[0] == socket.AF_INET]

socket.getaddrinfo = getaddrinfo_ipv4_only

USE_SUPABASE = os.getenv("USE_SUPABASE", "false").lower() == "true"

def get_connection():
    """
    Return a PostgreSQL connection based on USE_SUPABASE flag in environment variables.

    Supabase connections use SSL. Local Docker connections do not.
    """

    # Determine which database to use
    use_supabase = os.getenv("USE_SUPABASE", "false").lower() == "true"

    if use_supabase:
        host     = os.getenv("SUPABASE_POSTGRES_HOST")
        port     = int(os.getenv("SUPABASE_POSTGRES_PORT", 5432))
        database = os.getenv("SUPABASE_POSTGRES_DB")
        user     = os.getenv("SUPABASE_POSTGRES_USER")
        password = os.getenv("SUPABASE_POSTGRES_PASSWORD")
        sslmode  = "require"  # Supabase requires SSL
    else:
        host     = os.getenv("LOCAL_POSTGRES_HOST")
        port     = int(os.getenv("LOCAL_POSTGRES_PORT", 5432))
        database = os.getenv("LOCAL_POSTGRES_DB")
        user     = os.getenv("LOCAL_POSTGRES_USER")
        password = os.getenv("LOCAL_POSTGRES_PASSWORD")
        sslmode  = None

    # Check that all credentials are provided
    if not all([host, database, user, password]):
        print("❌ Missing database credentials. Please check your environment variables.")
        return None

    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            sslmode=sslmode,
            cursor_factory=RealDictCursor  # return dict-like rows
        )
        # Only print which DB, not sensitive info
        print(f"✅ Connected to {'Supabase' if use_supabase else 'Local Docker'} database")
        return conn
    except psycopg2.Error as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")
        return None
