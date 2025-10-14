import streamlit as st
import requests
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import logging
import os
import json

# --- Logging setup ---
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")

# --- Load config ---
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "config.json")
with open(config_path) as f:
    config = json.load(f)

# ================================
# 🌐 FX RATE FETCHER
# ================================
@st.cache_data(ttl=3600)
def get_fx_rate(currency: str):
    """Returns 1.0 for USD, else fetches USD->currency."""
    if currency.lower() == "usd":
        logging.info("get_fx_rate: USD -> USD (1.0)")
        return 1.0

    try:
        url = "https://open.er-api.com/v6/latest/USD"
        resp = requests.get(url, timeout=10).json()
        rate = resp.get("rates", {}).get(currency.upper(), 1.0)
        logging.info(f"get_fx_rate: USD -> {currency.upper()} = {rate}")
        return rate
    except Exception as e:
        logging.error(f"Failed to fetch FX rate for {currency}, default 1.0: {e}")
        return 1.0

# ================================
# 📈 STOCK DATA FETCHER
# ================================
@st.cache_data(ttl=3600)
def fetch_stock_data(ticker="AAPL", days=30, currency="usd"):
    """Fetch stock historical data + indicators."""
    try:
        end = datetime.today().date()
        start = end - timedelta(days=days)

        df = yf.download(ticker, start=start, end=end + timedelta(days=1),
                         progress=False, auto_adjust=True)
        if df.empty:
            logging.warning(f"No data returned for {ticker}")
            return pd.DataFrame(columns=["timestamp","price","MA7","MA30","daily_change","volatility"])

        # Flatten MultiIndex if exists
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = ["_".join(col).strip() if isinstance(col, tuple) else col for col in df.columns]

        df.reset_index(inplace=True)
        close_col = next((c for c in df.columns if "Close" in c), None)
        if close_col is None:
            logging.warning(f"No Close column found for {ticker}")
            return pd.DataFrame(columns=["timestamp","price","MA7","MA30","daily_change","volatility"])

        df = df[['Date', close_col]].rename(columns={'Date':'timestamp', close_col:'price'})

        # FX conversion
        fx_rate = get_fx_rate(currency)
        df["price"] = df["price"] * fx_rate

        # Rolling indicators
        window_7  = min(7, len(df))
        window_30 = min(30, len(df))
        df["MA7"] = df["price"].rolling(window=7, min_periods=1).mean()
        df["MA30"] = df["price"].rolling(window=30, min_periods=1).mean()
        df["daily_change"] = df["price"].pct_change() * 100
        df["volatility"]   = df["price"].rolling(window_7).std()

        df = df.dropna(subset=["price"]).reset_index(drop=True)
        logging.info(f"Fetched {ticker} {len(df)} rows from {start} to {end}")
        return df

    except Exception as e:
        logging.error(f"Error fetching stock data for {ticker}: {e}")
        return pd.DataFrame(columns=["timestamp","price","MA7","MA30","daily_change","volatility"])

# ================================
# 📊 SIMULATE STOCK INVESTMENT
# ================================
@st.cache_data(ttl=3600)
def simulate_stock_investment_curve(ticker="AAPL", invest_date=datetime(2024,1,1), amount=1000.0, currency="usd"):
    """Return portfolio evolution from invest_date until today."""
    today = datetime.today().date()
    invest_dt = invest_date.date() if isinstance(invest_date, datetime) else invest_date
    days = (today - invest_dt).days
    if days <= 0:
        logging.warning("Investment date is today or in the future; cannot simulate.")
        return pd.DataFrame(columns=["timestamp","portfolio_value","price"])

    df = fetch_stock_data(ticker, days, currency)
    df = df[df["timestamp"].dt.date >= invest_dt]
    if df.empty:
        logging.warning(f"No data after {invest_dt} for {ticker}")
        return pd.DataFrame(columns=["timestamp","portfolio_value","price"])

    start_price = df["price"].iloc[0]
    df["portfolio_value"] = amount * (df["price"] / start_price)
    return df[["timestamp","price","portfolio_value"]]
