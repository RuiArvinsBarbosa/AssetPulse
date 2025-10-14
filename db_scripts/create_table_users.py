from sqlalchemy import create_engine, Column, Integer, String, TIMESTAMP, MetaData, Table
from datetime import datetime
from sqlalchemy import text

# --- Database connection ---
engine = create_engine("postgresql+psycopg2://assetpulse:pass@localhost:5432/assetpulse")
metadata = MetaData()

# --- Define users table (with desired column order) ---
users_table = Table(
    "users", metadata,
    Column("username"     , String       , nullable=False),
    Column("email"        , String       , nullable=False),
    Column("user_ins"     , Integer      , nullable=True),
    Column("timestamp_ins", TIMESTAMP    , default=datetime.utcnow),
    Column("user_upd"     , String       , nullable=True),
    Column("timestamp_upd", TIMESTAMP    , onupdate=datetime.utcnow),
    Column("seq_no"       , Integer      , primary_key=True, autoincrement=True),
)

# --- Create table ---
metadata.create_all(engine)
print("Users table created successfully!")

# --- Create trigger function in PostgreSQL ---
with engine.connect() as conn:
    conn.execute(text("""
    CREATE OR REPLACE FUNCTION set_user_ins()
    RETURNS TRIGGER AS $$
    BEGIN
        UPDATE users
        SET user_ins = NEW.seq_no
        WHERE seq_no = NEW.seq_no;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """))

    # Drop old trigger if exists, then create the new one
    conn.execute(text("""
    DROP TRIGGER IF EXISTS trg_user_ins ON users;
    CREATE TRIGGER trg_user_ins
    AFTER INSERT ON users
    FOR EACH ROW
    EXECUTE FUNCTION set_user_ins();
    NOTICE:  trigger "trg_user_ins" for relation "users" does not exist, skipping
    DROP TRIGGER
    DROP FUNCTION
    CREATE FUNCTION
    CREATE TRIGGER
    """))

print("Trigger created successfully!")
