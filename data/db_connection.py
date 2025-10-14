import psycopg2
import os
from psycopg2.extras import RealDictCursor

def get_connection():
    """Return a PostgreSQL connection using environment variables."""
    host     = os.environ.get("POSTGRES_HOST", "localhost")
    port     = int(os.environ.get("POSTGRES_PORT", 5432))
    database = os.environ.get("POSTGRES_DB", "assetpulse")
    user     = os.environ.get("POSTGRES_USER", "assetpulse")
    password = os.environ.get("POSTGRES_PASSWORD", "pass")

    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            cursor_factory=RealDictCursor  # returns dict-like rows instead of tuples
        )
        return conn
    except psycopg2.Error as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")
        return None
