import streamlit as st
import requests
import pandas as pd
import os
import json
import yfinance as yf
from datetime import datetime, timedelta
import logging
import time

# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# --- Load config ---
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "config.json")
with open(config_path) as f:
    config = json.load(f)

@st.cache_data(ttl=3600)  # cache 1 hour
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


def fetch_stock_data(ticker="AAPL", days=30, currency="usd"):
    """Fetch historical stock data and convert to target currency."""
    try:
        # --- Use only date, no time ---
        end = datetime.today().date()
        start = end - timedelta(days=days)

        # --- Fetch stock in USD ---
        df = yf.download(ticker, start=start, end=end + timedelta(days=1), progress=False, auto_adjust=True)
        logging.info(f"Fetching {ticker} from {start} to {end}, raw rows: {len(df)}")

        if df.empty:
            logging.warning(f"No data returned for ticker {ticker}")
            return pd.DataFrame(columns=["timestamp", "price", "MA7", "MA30", "daily_change", "volatility"])

        # --- Flatten MultiIndex columns ---
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = ["_".join(col).strip() if isinstance(col, tuple) else col for col in df.columns]

        df.reset_index(inplace=True)

        # --- Find Close column dynamically ---
        close_col = next((c for c in df.columns if c.startswith("Close")), None)
        if not close_col:
            logging.warning(f"No 'Close' column found for {ticker}")
            return pd.DataFrame(columns=["timestamp", "price", "MA7", "MA30", "daily_change", "volatility"])

        # --- Keep only timestamp + price ---
        df = df[['Date', close_col]].rename(columns={'Date': 'timestamp', close_col: 'price'})

        # --- Convert USD to target currency ---
        fx_rate = get_fx_rate(currency)
        df["price"] = df["price"] * fx_rate

        # --- Calculate indicators ---
        df["MA7"] = df["price"].rolling(7).mean()
        df["MA30"] = df["price"].rolling(30).mean()
        df["daily_change"] = df["price"].pct_change() * 100
        df["volatility"] = df["price"].rolling(7).std()

        # Drop rows where moving averages are NaN
        df = df.dropna(subset=["MA7"])

        logging.info(f"Processed data rows: {len(df)}")
        return df

    except Exception as e:
        logging.error(f"Error fetching/processing stock data for {ticker}: {e}")
        return pd.DataFrame(columns=["timestamp", "price", "MA7", "MA30", "daily_change", "volatility"])
