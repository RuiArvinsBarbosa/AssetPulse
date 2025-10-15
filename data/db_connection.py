import psycopg2
import os
from psycopg2.extras import RealDictCursor

# ==========================================================
# 🔀 Database selection: choose 'local' or 'supabase'
# ==========================================================
DB_ENV = os.environ.get("DB_ENV", "local")  # options: "local" or "supabase"

def get_connection():
    """Return a PostgreSQL connection based on DB_ENV using environment variables only."""
    
    if DB_ENV == "supabase":
        host     = os.environ.get("SUPABASE_POSTGRES_HOST")
        port     = int(os.environ.get("SUPABASE_POSTGRES_PORT", 5432))
        database = os.environ.get("SUPABASE_POSTGRES_DB")
        user     = os.environ.get("SUPABASE_POSTGRES_USER")
        password = os.environ.get("SUPABASE_POSTGRES_PASSWORD")
    else:  # local Docker
        host     = os.environ.get("LOCAL_POSTGRES_HOST")
        port     = int(os.environ.get("LOCAL_POSTGRES_PORT", 5432))
        database = os.environ.get("LOCAL_POSTGRES_DB")
        user     = os.environ.get("LOCAL_POSTGRES_USER")
        password = os.environ.get("LOCAL_POSTGRES_PASSWORD")

    # Check that all required credentials are provided
    if not all([host, database, user, password]):
        print("❌ Missing database credentials. Please check your .env file or environment variables.")
        return None

    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            cursor_factory=RealDictCursor  # returns dict-like rows instead of tuples
        )
        print(f"✅ Connected to {'Supabase' if DB_ENV=='supabase' else 'Local Docker'} database")
        return conn
    except psycopg2.Error as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")
        return None
