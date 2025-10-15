import streamlit as st
from datetime import datetime, timedelta
import plotly.express as px
import pandas as pd
import json, os

# -------------------------------
# Project imports
# -------------------------------
from data.fetch_api_crypto import get_crypto_price_on_date, simulate_investment_curve
from data.fetch_api_stock  import simulate_stock_investment_curve

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
    st.warning("⚠️ COIN_MAP is empty! Define 'coin_map' in config/config.json.")

# -------------------------------
# User session check
# -------------------------------
current_user = st.session_state.get("current_user")
user_email   = st.session_state.get("user_email")
if "current_username" not in st.session_state or "username_email" not in st.session_state:
    st.warning("You must log in before accessing this page.")
    st.stop()

# -------------------------------
# Page config
# -------------------------------
st.set_page_config(
    page_title="AssetPulse – Portfolio Simulator",
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
col_title, col_user = st.columns([8, 4])
col_title.title("💰 Portfolio Simulator")
if current_user and user_email:
    col_user.markdown(f"**Logged in as:** {current_user} ({user_email})", unsafe_allow_html=True)

# -------------------------------
# Inputs
# -------------------------------
currency   = st.session_state.get("default_currency", CONFIG.get("defaults", {}).get("default_currency", "USD")).upper()
asset_type = st.radio("Asset type", ["CRYPTO", "STOCK"], horizontal=True)

symbol   = st.text_input(f"Enter asset symbol (e.g., BTC) [{currency}]:", "BTC").upper()
max_date = datetime.today().date() - timedelta(days=365)
invest_date     = st.date_input("Select investment date", value=max_date, max_value=datetime.today().date(), min_value=max_date)
amount_invested = st.number_input(f"Amount invested on {invest_date} ({currency}):", min_value=1.0, value=1000.0, step=100.0)

# -------------------------------
# Simulation
# -------------------------------
if st.button("Simulate Investment"):
    if invest_date > datetime.today().date():
        st.warning("Investment date cannot be in the future.")
    else:
        # Fetch historical portfolio data
        if asset_type == "CRYPTO":
            df_prices = simulate_investment_curve(symbol, invest_date, amount_invested, currency.lower())
        else:
            df_prices = simulate_stock_investment_curve(symbol, invest_date, amount_invested, currency.upper())

        if df_prices.empty:
            st.warning("Could not fetch historical data for the selected asset.")
        else:
            df_prices = df_prices[df_prices["timestamp"].dt.date >= invest_date]
            if df_prices.empty:
                st.warning("No price data available after the selected investment date.")
            else:
                start_price = df_prices["price"].iloc[0]
                df_prices["portfolio_value"] = amount_invested * (df_prices["price"] / start_price)
                final_value = df_prices["portfolio_value"].iloc[-1]

                st.markdown(f"💰 Your investment of {amount_invested:.2f} {currency} on {invest_date} "
                            f"would be worth {final_value:.2f} {currency} today")

                fig = px.line(
                    df_prices, x="timestamp", y="portfolio_value",
                    title=f"Portfolio Simulation: {amount_invested} {currency} in {symbol}",
                    labels={"portfolio_value": f"Portfolio Value ({currency})", "timestamp": "Date"},
                    template="plotly_white"
                )
                st.plotly_chart(fig, use_container_width=True)
