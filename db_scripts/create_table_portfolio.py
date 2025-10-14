from sqlalchemy import create_engine, Column, Integer, String, Numeric, TIMESTAMP, MetaData, Table
from datetime   import datetime

# --- Database connection ---
engine = create_engine("postgresql+psycopg2://assetpulse:pass@localhost:5432/assetpulse")
metadata = MetaData()

# --- Define portfolio table ---
portfolio_table = Table(
    "portfolio", metadata,
    Column("id"           , Integer      , nullable=False                      ),
    Column("user"         , String       , nullable=False                      ),
    Column("asset_type"   , String       , nullable=False                      ), # "STOCK" or "CRYPTO"
    Column("asset_code"   , String       , nullable=False                      ), # "GOOGL" or "BTC"
    Column("quantity"     , Numeric(12,4), nullable=False                      ),
    Column("price"        , Numeric(12,2), nullable=False                      ),
    Column("timestamp_buy", TIMESTAMP    , nullable=False                      ),
    Column("user_ins"     , String       , nullable=False                      ),
    Column("timestamp_ins", TIMESTAMP    , default=datetime.utcnow             ),
    Column("user_upd"     , String       , nullable=True                       ),
    Column("timestamp_upd", TIMESTAMP    , onupdate=datetime.utcnow            ),
    Column("seq_no"       , Integer      , primary_key=True, autoincrement=True),
)

# --- Create table ---
metadata.create_all(engine)
print("Portfolio table created successfully!")
