# ==========================================================
# db_connection.py
# ==========================================================
# Handles PostgreSQL connections for both local Docker and Supabase.
# Uses environment variables and automatically applies SSL for Supabase.
# ==========================================================
import psycopg2
import os
from psycopg2.extras import RealDictCursor

USE_SUPABASE = os.getenv("USE_SUPABASE", "false").lower() == "true"

def get_connection():
    """
    Return a PostgreSQL connection based on USE_SUPABASE flag.

    - Local dev: Direct Connection or Docker
    - Render: Session Pooler (IPv4)
    """
    if USE_SUPABASE:
        if os.getenv("RENDER") == "true":
            # Session Pooler for Render
            host     = os.getenv("SUPABASE_POOLER_HOST")
            port     = int(os.getenv("SUPABASE_POOLER_PORT", 5432))
            database = os.getenv("SUPABASE_POOLER_DB")
            user     = os.getenv("SUPABASE_POOLER_USER")
            password = os.getenv("SUPABASE_POOLER_PASSWORD")
        else:
            # Direct Connection for local dev
            host     = os.getenv("SUPABASE_DIRECT_HOST")
            port     = int(os.getenv("SUPABASE_DIRECT_PORT", 5432))
            database = os.getenv("SUPABASE_DIRECT_DB")
            user     = os.getenv("SUPABASE_DIRECT_USER")
            password = os.getenv("SUPABASE_DIRECT_PASSWORD")

        sslmode = "require"
    else:
        # Local Docker
        host     = os.getenv("LOCAL_POSTGRES_HOST")
        port     = int(os.getenv("LOCAL_POSTGRES_PORT", 5432))
        database = os.getenv("LOCAL_POSTGRES_DB")
        user     = os.getenv("LOCAL_POSTGRES_USER")
        password = os.getenv("LOCAL_POSTGRES_PASSWORD")
        sslmode = None

    # Debug: print all credentials being used (do not print password in prod)
    # print(f"DEBUG: Connecting to {host}:{port} db={database} user={user}")

    # Check all required variables
    if not all([host, database, user, password]):
        raise ValueError("❌ Missing database credentials. Check environment variables.")

    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            sslmode=sslmode,
            cursor_factory=RealDictCursor
        )
        # print(f"✅ Connected to {'Supabase' if USE_SUPABASE else 'Local Docker'} database at {host}")
        return conn
    except psycopg2.Error as e:
        raise ConnectionError(f"❌ Failed to connect to PostgreSQL: {e}")