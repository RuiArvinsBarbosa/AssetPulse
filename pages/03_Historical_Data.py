import streamlit as st
import pandas as pd
import requests
import yfinance as yf
import json, os
from data.table_transactions_crud import fetch_all_user_transactions
from dotenv import load_dotenv

# -------------------------------
# Load config.json
# -------------------------------
BASE_DIR    = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "config.json")

if not os.path.exists(CONFIG_PATH):
    st.error(f"Config file not found at {CONFIG_PATH}.")
    st.stop()

with open(CONFIG_PATH, "r") as f:
    CONFIG = json.load(f)

COIN_MAP = CONFIG.get("coin_map", {})
if not COIN_MAP:
    st.warning("⚠️ COIN_MAP is empty! Check your config.json")

# -------------------------------
# User session check
# -------------------------------
current_user = st.session_state.get("current_user")
user_email   = st.session_state.get("user_email")
user_seq_no  = st.session_state.get("user_seq_no")
if "current_username" not in st.session_state or "username_email" not in st.session_state:
    st.warning("You must log in before accessing this page.")
    st.stop()

# -------------------------------
# Page config
# -------------------------------
st.set_page_config(
    page_title="AssetPulse – Historical Transactions",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------
# THEME SETTINGS
# -------------------------------
theme = st.session_state.get("app_theme")
if theme is None:
    theme = os.getenv("APP_THEME", "Light") # fallback to "Light" if not in .env
    st.session_state["app_theme"] = theme   # store in session_state for consistency

bg_color, text_color, btn_bg, btn_text = (
    ("#0E1117", "white", "#444", "white") if theme == "Dark" else ("white", "black", "#eee", "black")
)

st.markdown(f"""
    <style>
    .css-18e3th9, .css-1outpf7, .css-1d391kg {{
        background-color: {bg_color} !important;
        color: {text_color} !important;
    }}
    .stButton>button {{
        background-color: {btn_bg};
        color: {btn_text};
    }}
    </style>
""", unsafe_allow_html=True)

# -------------------------------
# Page header
# -------------------------------
col_title, col_user = st.columns([8,4])
col_title.title("🗄️ Historical Transactions")
if current_user and user_email:
    col_user.markdown(f"**Logged in as:** {current_user} ({user_email})", unsafe_allow_html=True)

st.markdown("View all your transactions grouped by asset type with current value.")

# -------------------------------
# Fetch transactions
# -------------------------------
try:
    all_tx = fetch_all_user_transactions(user_seq_no)
    if not all_tx:
        st.info("No transactions available.")
        st.stop()

    df_tx = pd.DataFrame(all_tx, columns=[
        "portfolio_seq_no","in_out","user_seq_no","asset_type","asset_code",
        "quantity","price","currency","timestamp_txn","user_ins",
        "timestamp_ins","user_upd","timestamp_upd","seq_no"
    ])
    df_tx = df_tx[df_tx["user_seq_no"]==user_seq_no]
    if df_tx.empty:
        st.info("No transactions for your account.")
        st.stop()
except Exception as e:
    st.error(f"Error fetching transactions: {e}")
    st.stop()

# -------------------------------
# Price fetching with caching
# -------------------------------
@st.cache_data(ttl=600)
def get_current_price_crypto(symbol: str, currency="USD"):
    coin_id = COIN_MAP.get(symbol.upper(), symbol.lower())
    try:
        resp = requests.get("https://api.coingecko.com/api/v3/simple/price",
                            params={"ids": coin_id,"vs_currencies": currency.lower()},
                            timeout=10).json()
        price = resp.get(coin_id, {}).get(currency.lower())
        return float(price) if price else None
    except Exception as e:
        st.warning(f"Failed to fetch {symbol}: {e}")
        return None

@st.cache_data(ttl=600)
def get_current_price_stock(symbol: str):
    try:
        data = yf.Ticker(symbol).history(period="1d")
        return float(data["Close"].iloc[-1]) if not data.empty else None
    except:
        return None

# -------------------------------
# Add current value, price & variation
# -------------------------------
def add_current_value(df):
    df_display = df.copy()
    df_display["current_price"] = df_display.apply(
        lambda r: get_current_price_crypto(r["asset_code"]) if r["asset_type"].upper()=="CRYPTO"
        else get_current_price_stock(r["asset_code"]), axis=1
    )
    df_display["variation_%"] = df_display.apply(
        lambda r: ((float(r["current_price"])-float(r["price"]))/float(r["price"])*100) 
        if r["current_price"] is not None else None, axis=1
    )
    df_display["current_value"] = df_display.apply(
        lambda r: float(r["current_price"])*float(r["quantity"]) if r["current_price"] else None, axis=1
    )
    df_display["timestamp_txn"] = df_display["timestamp_txn"].dt.strftime("%Y-%m-%d %H:%M")
    return df_display

# -------------------------------
# Process transactions
# -------------------------------
try:
    df_all = add_current_value(df_tx)
except Exception as e:
    st.error(f"Error processing transactions: {e}")
    st.stop()

if df_all.empty:
    st.info("No transactions to display.")
    st.stop()

# -------------------------------
# Display by asset type
# -------------------------------
for asset_type in df_all["asset_type"].str.upper().unique():
    st.subheader(f"📊 {asset_type} Transactions")
    df_group = df_all[df_all["asset_type"].str.upper()==asset_type]
    display_df = df_group[[
        "asset_type","asset_code","quantity","price","currency","timestamp_txn",
        "current_price","variation_%","current_value"
    ]].sort_values("timestamp_txn").reset_index(drop=True)
    fmt_cols = {col:"{:,.2f}" for col in ["quantity","price","current_price","variation_%","current_value"]}
    st.dataframe(display_df.style.format(fmt_cols))
