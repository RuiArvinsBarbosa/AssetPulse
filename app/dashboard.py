import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import streamlit as st
import plotly.express as px
import numpy as np
from sklearn.linear_model import LinearRegression
import json

from data.fetch_api_stock  import fetch_stock_data
from data.fetch_api_crypto import fetch_crypto_data
from data.db_ins           import log_price, log_prices, fetch_history  # PostgreSQL functions

import logging

# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# ==========================================================
# 🟢 FX RATE CACHE FUNCTION
# ==========================================================
@st.cache_data(ttl=3600)
def get_fx_rate(currency: str):
    if currency.lower() == "usd":
        return 1.0
    try:
        url = "https://api.coingecko.com/api/v3/exchange_rates"
        data = requests.get(url, timeout=10).json()
        rate = data["rates"][currency.lower()]["value"]
        return rate
    except Exception as e:
        logging.error(f"Failed to fetch FX rate for {currency}, defaulting to 1.0: {e}")
        return 1.0

# ==========================================================
# 🧠 CONFIGURATION: ENV VARIABLES FIRST, FALLBACK TO config.json
# ==========================================================
config_path = "config/config.json"
with open(config_path) as f:
    local_config = json.load(f)

# --- Coins and Stocks ---
coins_env  = os.environ.get("COINS")
stocks_env = os.environ.get("STOCKS")
config_coins  = coins_env.split(",") if coins_env else local_config.get("coins", ["bitcoin", "ethereum", "litecoin"])
config_stocks = stocks_env.split(",") if stocks_env else local_config.get("stocks", ["AAPL", "MSFT", "GOOGL"])

# --- Currencies ---
vs_currency = os.environ.get("VS_CURRENCY", local_config.get("vs_currency", "usd"))
currencies_env = os.environ.get("CURRENCIES")
config_currencies = currencies_env.split(",") if currencies_env else local_config.get("currencies", ["usd", "eur", "gbp"])

# --- Days of historical data ---
days = int(os.environ.get("DAYS", local_config.get("days", 30)))

# ==========================================================
# 🧪 STREAMLIT DASHBOARD SETUP
# ==========================================================
st.title("AssetPulse MVP – Crypto & Stock Dashboard")

# --- Select asset type ---
asset_type = st.radio("Asset type", ["Crypto", "Stock"], key="asset_type_select")

# --- Select currency ---
selected_currency = st.selectbox(
    "Select currency",
    config_currencies,
    index=config_currencies.index(vs_currency)
)

# --- Initialize variables ---
symbol = None
df     = None
title  = ""

# ==========================================================
# 🟢 CACHE WRAPPER FOR CRYPTO DATA
# ==========================================================
@st.cache_data(ttl=3600)  # 1 hour
def get_crypto_data_cached(coin_id, days, vs_currency):
    """Cache wrapper for crypto data fetching."""
    return fetch_crypto_data(coin_id=coin_id, days=days, vs_currency=vs_currency)

# ==========================================================
# 📈 DATA FETCHING
# ==========================================================
if asset_type == "Crypto":
    symbol = st.selectbox("Select cryptocurrency", config_coins, key="crypto_select")
    # Pass selected_currency from UI
    df = get_crypto_data_cached(
        coin_id=symbol,
        days=days,
        vs_currency=selected_currency.lower()  # lowercase ensures CoinGecko compatibility
    )
    title = f"{symbol.capitalize()} Price & Indicators ({selected_currency.upper()})"

elif asset_type == "Stock":
    symbol = st.selectbox("Select stock", config_stocks, key="stock_select")
    # Pass selected_currency from UI for FX conversion
    df = fetch_stock_data(ticker=symbol, days=days, currency=selected_currency.lower())
    title = f"{symbol} Stock Price & Indicators ({selected_currency.upper()})"

# ==========================================================
# 🧮 DATA DISPLAY AND INDICATORS
# ==========================================================
if df is None or df.empty or symbol is None:
    st.warning("No data available for the selected asset.")
else:
    # --- Log latest price to PostgreSQL ---
    latest_price = float(df["price"].iloc[-1])
    try:
        log_price(symbol, latest_price)
    except Exception as e:
        st.error(f"Error logging price: {e}")

    # --- Visualization options ---
    show_ma_07      = st.checkbox("Show 7-day moving average")
    show_ma_30      = st.checkbox("Show 30-day moving average")
    show_trend      = st.checkbox("Show trend (linear fit)")
    show_volatility = st.checkbox("Show volatility")

    # --- Prepare Y columns dynamically ---
    y_columns = ["price"]
    if show_ma_07 and "MA7" in df.columns and df["MA7"].notna().any():
        y_columns.append("MA7")
    if show_ma_30 and "MA30" in df.columns and df["MA30"].notna().any():
        y_columns.append("MA30")
    if show_volatility and "volatility" in df.columns and df["volatility"].notna().any():
        y_columns.append("volatility")

    # --- Main Chart ---
    fig = px.line(df, x="timestamp", y=y_columns, title=title, labels={"value": "Price / Indicator"})
    fig.update_traces(mode="lines+markers", hovertemplate='%{y:.2f} at %{x}')

    # --- Trend Line (Linear Regression) ---
    if show_trend:
        x_numeric = np.arange(len(df)).reshape(-1, 1)
        model = LinearRegression().fit(x_numeric, df["price"])
        df["trend"] = model.predict(x_numeric)
        fig.add_scatter(x=df["timestamp"], y=df["trend"], mode="lines", name="Trend")

    st.plotly_chart(fig, use_container_width=True)

    # --- Recent data table ---
    st.subheader("Recent data")
    st.dataframe(df.tail(10))

# ==========================================================
# 💰 Portfolio Simulator
# ==========================================================
    st.subheader("Portfolio Simulator 💰")
    initial_investment = st.number_input(
        f"Enter amount to invest ({selected_currency.upper()}):",
        min_value=1.0, value=1000.0, step=100.0
    )
    if st.button("Simulate Investment"):
        start_price = df["price"].iloc[0]
        df["portfolio_value"] = df["price"] / start_price * initial_investment
        fig_portfolio = px.line(
            df, x="timestamp", y="portfolio_value",
            title=f"Portfolio Value Simulation ({initial_investment} invested in {symbol})",
            labels={"portfolio_value": "Portfolio Value", "timestamp": "Date"}
        )
        st.plotly_chart(fig_portfolio, use_container_width=True)

# ==========================================================
# 🗄️ PostgreSQL Historical Data
# ==========================================================
    st.subheader(f"Historical Prices (PostgreSQL): ({selected_currency.upper()})")
    try:
        history = fetch_history(symbol)
        if history:
            timestamps, prices = zip(*history)
            fig_hist = px.line(
                x=timestamps, y=prices,
                title=f"{symbol} Historical Prices (PostgreSQL)",
                labels={"x": "Timestamp", "y": "Price"}
            )
            st.plotly_chart(fig_hist, use_container_width=True)

            st.subheader("Recent Logged Prices")
            st.table([{"Timestamp": ts, f"Price ({selected_currency.upper()})": p} for ts, p in history[-10:]])
        else:
            st.write("No historical data yet.")
    except Exception as e:
        st.error(f"Error fetching historical data: {e}")
