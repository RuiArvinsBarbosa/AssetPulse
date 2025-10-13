import streamlit as st

# Must be at the very top of your app, before any other Streamlit commands
st.set_page_config(
    page_title="AssetPulse Dashboard",
    layout="wide",        # <-- makes full-width layout
    initial_sidebar_state="expanded"
)

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import streamlit as st
import plotly.express as px
import numpy as np
from sklearn.linear_model import LinearRegression
import pandas as pd
import requests
import json
import logging
import time
import random
from datetime import datetime, timedelta

from data.fetch_api_stock  import fetch_stock_data
from data.fetch_api_crypto import fetch_crypto_data
from data.db_ins           import log_price, fetch_history  # PostgreSQL functions

# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# ==========================================================
# 🟢 CRYPTO DATA FETCH FUNCTION WITH FX CONVERSION
# ==========================================================
@st.cache_data(ttl=3600)
def fetch_crypto_data_cached(coin_id, vs_currency, days):
    """Fetch crypto data from CoinGecko with retry and FX support."""
    coin_id = coin_id.lower()
    vs_currency = vs_currency.lower()
    days = int(days)

    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": vs_currency, "days": days}
    delay = 2
    max_delay = 60
    max_retries = 5

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            prices = data.get("prices", [])
            if not prices:
                logging.warning(f"No price data returned for {coin_id}")
                return pd.DataFrame(columns=["timestamp", "price"])
            df = pd.DataFrame(prices, columns=["timestamp", "price"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            return df
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                jitter = random.uniform(0, 1)
                logging.warning(f"Rate limited for {coin_id}, retry {attempt}/{max_retries} in {delay+jitter:.1f}s...")
                time.sleep(min(delay + jitter, max_delay))
                delay = min(delay * 2, max_delay)
            else:
                logging.error(f"HTTP error for {coin_id}: {e}")
                break
        except requests.exceptions.RequestException as e:
            jitter = random.uniform(0, 1)
            logging.error(f"Network/API error for {coin_id}, retry {attempt}/{max_retries} in {delay+jitter:.1f}s: {e}")
            time.sleep(min(delay + jitter, max_delay))
            delay = min(delay * 2, max_delay)

    logging.error(f"Failed to fetch data for {coin_id} after {max_retries} retries.")
    return pd.DataFrame(columns=["timestamp", "price"])

# ==========================================================
# 🧠 CONFIGURATION
# ==========================================================
config_path = "config/config.json"
with open(config_path) as f:
    local_config = json.load(f)

coins_env  = os.environ.get("COINS")
stocks_env = os.environ.get("STOCKS")
config_coins  = coins_env.split(",") if coins_env else local_config.get("coins", ["bitcoin","ethereum","litecoin"])
config_stocks = stocks_env.split(",") if stocks_env else local_config.get("stocks", ["AAPL","MSFT","GOOGL"])

vs_currency = os.environ.get("VS_CURRENCY", local_config.get("vs_currency", "usd"))
currencies_env = os.environ.get("CURRENCIES")
config_currencies = currencies_env.split(",") if currencies_env else local_config.get("currencies", ["usd","eur","gbp"])

days = int(os.environ.get("DAYS", local_config.get("days", 30)))

# ==========================================================
# 🧪 STREAMLIT DASHBOARD SETUP
# ==========================================================
st.title("AssetPulse MVP – Crypto & Stock Dashboard")

asset_type = st.radio("Asset type", ["Crypto", "Stock"], key="asset_type_select")

selected_currency = st.selectbox(
    "Select currency",
    config_currencies,
    index=config_currencies.index(vs_currency)
)

symbol = None
df = None
title = ""

# ==========================================================
# 📈 DATA FETCHING
# ==========================================================
if asset_type == "Crypto":
    symbol = st.selectbox("Select cryptocurrency", config_coins, key="crypto_select")
    df = fetch_crypto_data(
        coin_id=symbol,
        days=days,
        currency=selected_currency.lower()
    )
    # Fallback FX conversion if CoinGecko fails to return selected currency
    if df.empty and selected_currency.lower() != "usd":
        logging.info(f"Falling back to USD → {selected_currency.upper()} conversion")
        df_usd = fetch_crypto_data_cached(coin_id=symbol, vs_currency="usd", days=days)
        fx = get_fx_rate(selected_currency)
        df = df_usd.copy()
        df["price"] = df["price"] * fx

    # Indicators
    df["MA7"] = df["price"].rolling(7).mean()
    df["MA30"] = df["price"].rolling(30).mean()
    df["daily_change"] = df["price"].pct_change() * 100
    df["volatility"] = df["price"].rolling(7).std()
    df = df.dropna(subset=["MA7"])
    title = f"{symbol.capitalize()} Price & Indicators ({selected_currency.upper()})"

elif asset_type == "Stock":
    symbol = st.selectbox("Select stock", config_stocks, key="stock_select")
    df = fetch_stock_data(ticker=symbol, days=days, currency=selected_currency.lower())
    title = f"{symbol} Stock Price & Indicators ({selected_currency.upper()})"

# ==========================================================
# 🧮 DATA DISPLAY AND INDICATORS
# ==========================================================
if df is None or df.empty or symbol is None:
    st.warning("No data available for the selected asset.")
else:
    latest_price = float(df["price"].iloc[-1])
    try:
        log_price(symbol, latest_price)
    except Exception as e:
        st.error(f"Error logging price: {e}")

    show_ma_07      = st.checkbox("Show 7-day moving average")
    show_ma_30      = st.checkbox("Show 30-day moving average")
    show_trend      = st.checkbox("Show trend (linear fit)")
    show_volatility = st.checkbox("Show volatility")

    y_columns = ["price"]
    if show_ma_07 and "MA7" in df.columns: y_columns.append("MA7")
    if show_ma_30 and "MA30" in df.columns: y_columns.append("MA30")
    if show_volatility and "volatility" in df.columns: y_columns.append("volatility")

    fig = px.line(df, x="timestamp", y=y_columns, title=title, labels={"value": "Price / Indicator"})
    fig.update_traces(mode="lines+markers", hovertemplate='%{y:.2f} at %{x}')
    fig.update_yaxes(tickformat=".2f")  # mostra sempre 2 casas decimais

    if show_trend:
        x_numeric = np.arange(len(df)).reshape(-1, 1)
        model = LinearRegression().fit(x_numeric, df["price"])
        df["trend"] = model.predict(x_numeric)
        fig.add_scatter(x=df["timestamp"], y=df["trend"], mode="lines", name="Trend")

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Recent data")
    st.dataframe(df.style.format({"price": "{:,.2f}"}))  # duas casas decimais, separador de milhar

# ==========================================================
# 💰 Portfolio Simulator
# ==========================================================
#    st.subheader("Portfolio Simulator 💰")
#    initial_investment = st.number_input(
#        f"Enter amount to invest ({selected_currency.upper()}):",
#        min_value=1.0, value=1000.0, step=100.0
#    )
#    if st.button("Simulate Investment"):
#        start_price = df["price"].iloc[0]
#        df["portfolio_value"] = df["price"] / start_price * initial_investment
#        fig_portfolio = px.line(
#            df, x="timestamp", y="portfolio_value",
#            title=f"Portfolio Value Simulation ({initial_investment} invested in {symbol})",
#            labels={"portfolio_value": "Portfolio Value", "timestamp": "Date"}
#        )
#        st.plotly_chart(fig_portfolio, use_container_width=True)

# ==========================================================
# 🗄️ PostgreSQL Historical Data
# ==========================================================
#    st.subheader(f"Historical Prices (PostgreSQL): ({selected_currency.upper()})")
#    try:
#        history = fetch_history(symbol)
#        if history:
#            timestamps, prices = zip(*history)
#            fig_hist = px.line(
#                x=timestamps, y=prices,
#                title=f"{symbol} Historical Prices (PostgreSQL)",
#                labels={"x": "Timestamp", "y": "Price"}
#            )
#            st.plotly_chart(fig_hist, use_container_width=True)
#
#            st.subheader("Recent Logged Prices")
#            st.table([{"Timestamp": ts, f"Price ({selected_currency.upper()})": p} for ts, p in history[-10:]])
#        else:
#            st.write("No historical data yet.")
#    except Exception as e:
#        st.error(f"Error fetching historical data: {e}")
