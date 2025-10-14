import streamlit      as st
import plotly.express as px
import numpy          as np
from sklearn.linear_model import LinearRegression
import pandas as pd
import logging, os, sys, json, warnings
from datetime import datetime, timedelta
import requests

# -------------------------------
# Load .env first
# -------------------------------
from dotenv import load_dotenv
load_dotenv()

# -------------------------------
# Add project root to path
# -------------------------------
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.fetch_api_stock import fetch_stock_data
from data.fetch_api_crypto import fetch_crypto_data
from data.table_transactions_crud import insert_transaction, fetch_transactions_by_user_asset

warnings.simplefilter("ignore", FutureWarning)

# -------------------------------
# User session
# -------------------------------
current_user = st.session_state.get("current_user")
user_email   = st.session_state.get("user_email")
user_seq_no  = st.session_state.get("user_seq_no")

# -------------------------------
# PAGE CONFIG & LOGIN CHECK
# -------------------------------
if "current_username" not in st.session_state or "username_email" not in st.session_state:
    st.warning("You must log in before accessing this page.")
    st.stop()

st.set_page_config(
    page_title="AssetPulse – Dashboard",
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
# CONFIGURATION
# -------------------------------
with open("config/config.json") as f:
    local_config = json.load(f)

# Coins and stocks only come from JSON now
config_coins      = local_config.get("coins", [])
config_stocks     = local_config.get("stocks", [])
config_currencies = local_config.get("currencies", [])

selected_currency = st.session_state.get("default_currency", local_config.get("defaults", {}).get("default_currency","USD")).lower()
days = int(os.getenv("DAYS", local_config.get("days", 30)))
data_refresh_rate = int(os.getenv("DATA_REFRESH_RATE", local_config.get("defaults", {}).get("data_refresh_rate", 15)))

# -------------------------------
# PAGE HEADER
# -------------------------------
col_title, col_user = st.columns([8,4])
col_title.title("AssetPulse – Crypto & Stock Dashboard")

if current_user and user_email:
    col_user.markdown(f"**Logged in as:** {current_user} ({user_email})", unsafe_allow_html=True)

asset_type = st.radio("Asset type", ["CRYPTO","STOCK"], key="asset_type_select", horizontal=True)
title, asset_code, df = "", "", pd.DataFrame()

# -------------------------------
# FETCH DATA
# -------------------------------
if asset_type=="CRYPTO":
    asset_code = st.selectbox("Select cryptocurrency", config_coins, key="crypto_select")
    df = fetch_crypto_data(asset_code, days, selected_currency)
    
    if df.empty and selected_currency!="usd":
        df_usd = fetch_crypto_data(asset_code, days, "usd")
        df = df_usd.copy()
        df["price"] *= 1.0  # TODO: apply FX conversion
    
    df["MA7"], df["MA30"] = df["price"].rolling(7).mean(), df["price"].rolling(30).mean()
    df["daily_change"], df["volatility"] = df["price"].pct_change()*100, df["price"].rolling(7).std()
    df.dropna(subset=["MA7"], inplace=True)
    title = f"{asset_code.capitalize()} Price & Indicators ({selected_currency.upper()})"

elif asset_type=="STOCK":
    asset_code = st.selectbox("Select stock", config_stocks, key="stock_select")
    df = fetch_stock_data(asset_code, days, selected_currency)
    title = f"{asset_code} Stock Price & Indicators ({selected_currency.upper()})"

# -------------------------------
# DISPLAY DATA
# -------------------------------
if df.empty or asset_code=="":
    st.warning("No data available for the selected asset.")
else:
    latest_price = float(df["price"].iloc[-1])


    # Indicators
    col1,col2  = st.columns(2)
    show_ma_07 = col1.checkbox("7-day MA")
    show_ma_30 = col2.checkbox("30-day MA")
    col3,col4  = st.columns(2)
    show_trend      = col3.checkbox("Trend (Linear Fit)")
    show_volatility = col4.checkbox("Volatility")

    y_cols = ["price"]
    if show_ma_07 and "MA7"  in df: y_cols.append("MA7")
    if show_ma_30 and "MA30" in df: y_cols.append("MA30")
    if show_volatility and "volatility" in df: y_cols.append("volatility")

    fig = px.line(df, x="timestamp", y=y_cols, title=title)
    if show_trend:
        x_num = np.arange(len(df)).reshape(-1,1)
        df["trend"] = LinearRegression().fit(x_num, df["price"]).predict(x_num)
        fig.add_scatter(x=df["timestamp"], y=df["trend"], mode="lines", name="Trend")
    st.plotly_chart(fig, use_container_width=True)

    # Recent data table
    st.subheader("Recent data")
    recent_df = df.tail(10).copy()
    recent_df["timestamp"] = recent_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M")
    st.dataframe(recent_df.style.format({c:"{:,.2f}" for c in recent_df.columns if c!="timestamp"}))

# -------------------------------
# USER PORTFOLIO MANAGEMENT
# -------------------------------
st.subheader("Manage Ownership")
if "portfolio" not in st.session_state or not isinstance(st.session_state["portfolio"], dict):
    st.session_state["portfolio"] = {"STOCK":{}, "CRYPTO":{}}
else:
    for k in ["STOCK","CRYPTO"]:
        if k not in st.session_state["portfolio"] or not isinstance(st.session_state["portfolio"][k], dict):
            st.session_state["portfolio"][k] = {}

quantity = st.number_input(f"Quantity for {asset_code.upper()}", min_value=0.0, step=1.0)
col_buy,col_sell = st.columns(2)

with col_buy:
    if st.button(f"Add {asset_code.upper()}", key=f"buy_{asset_code}_{asset_type}"):
        try:
            insert_transaction(0,1,user_seq_no,asset_type,asset_code.upper(),quantity,float(df["price"].iloc[-1]),selected_currency.upper(),user_seq_no)
        except Exception as e:
            st.error(f"Error inserting transaction: {e}")

with col_sell:
    if st.button(f"Remove {asset_code.upper()}", key=f"sell_{asset_code}_{asset_type}"):
        try:
            insert_transaction(99,0,user_seq_no,asset_type,asset_code.upper(),quantity,float(df["price"].iloc[-1]),selected_currency.upper(),user_seq_no)
        except Exception as e:
            st.error(f"Error inserting transaction: {e}")

# -------------------------------
# FETCH AND DISPLAY TRANSACTIONS
# -------------------------------
if user_seq_no is None:
    st.warning("User not logged in. Cannot fetch transactions.")
else:
    try:
        st.subheader(f"Transactions for user '{user_seq_no}' ({asset_code.upper()})")
        transactions = fetch_transactions_by_user_asset(asset_code.upper(), user_seq_no)
        print(f"transactions={transactions}")
        if transactions:
            display_data = [
                {
                    "In/Out": "BUY" if t["in_out"] == 1 else "SELL",
                    "Asset Type": t["asset_type"],
                    "Asset Code": t["asset_code"],
                    "Quantity": float(t["quantity"]),
                    "Price": float(t["price"]),
                    "Currency": t["currency"],
                    "Timestamp": t["timestamp_txn"].strftime("%Y-%m-%d %H:%M")
                }
                for t in transactions
            ]
            
            st.table(display_data)
        else:
            st.info("No transactions found for the selected user and asset type.")
    except Exception as e:
        st.error(f"Error fetching transactions: {e}")
