from sqlalchemy import create_engine, Column, Integer, String, Numeric, TIMESTAMP, MetaData, Table
from datetime   import datetime

# --- Database connection ---
engine   = create_engine("postgresql+psycopg2://assetpulse:pass@localhost:5432/assetpulse")
metadata = MetaData()

# --- Define buy/sell transactions table ---
transactions_table = Table(
    "transactions", metadata,
    Column("portfolio_seq_no", Integer      , nullable=False                         ), # unique ID
    Column("in_out"          , Integer      , nullable=False                         ), # buy = 1 /sell = 0
    Column("user_seq_no"     , Integer      , nullable=False                         ), # user making the transaction
    Column("asset_type"      , String       , nullable=False                         ), # "STOCK" or "CRYPTO"
    Column("asset_code"      , String       , nullable=False                         ), # e.g., "GOOGL" or "BTC"
    Column("quantity"        , Numeric(12,4), nullable=False                         ),
    Column("price"           , Numeric(12,2), nullable=False                         ),
    Column("currency"        , String       , nullable=False                         ),
    Column("timestamp_txn"   , TIMESTAMP    , nullable=False, default=datetime.utcnow), # when transaction happened
    Column("user_ins"        , String       , nullable=False                         ), # who inserted the record
    Column("timestamp_ins"   , TIMESTAMP    , default=datetime.utcnow                ), # when record inserted
    Column("user_upd"        , String       , nullable=True                          ), # who last updated
    Column("timestamp_upd"   , TIMESTAMP    , onupdate=datetime.utcnow               ), # last update time
    Column("seq_no"          , Integer      , primary_key=True, autoincrement=True   ), # sequential number
)

# --- Create table ---
metadata.create_all(engine)
print("Transactions table created successfully!")
