import streamlit as st
import requests
import pandas as pd
import os
import json
import yfinance as yf
from datetime import datetime, timedelta
import logging

# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# --- Load config ---
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "config.json")
with open(config_path) as f:
    config = json.load(f)

@st.cache_data(ttl=3600)
def get_fx_rate(currency: str):
    """
    Returns 1.0 for USD, otherwise fetches USD -> target currency using a free API.
    Uses https://open.er-api.com (no API key required).
    """
    if currency.lower() == "usd":
        logging.info("get_fx_rate currency-> USD (default 1.0)")
        return 1.0

    try:
        url = "https://open.er-api.com/v6/latest/USD"
        response = requests.get(url, timeout=10)
        data = response.json()

        if "rates" in data and currency.upper() in data["rates"]:
            rate = data["rates"][currency.upper()]
            logging.info(f"get_fx_rate USD->{currency.upper()} = {rate}")
            return rate
        else:
            logging.warning(f"Unexpected FX response: {data}")
            return 1.0

    except Exception as e:
        logging.error(f"Failed to fetch FX rate for {currency}, defaulting to 1.0: {e}")
        return 1.0

# --- Stock fetcher ---
@st.cache_data(ttl=3600)
def fetch_stock_data(ticker="AAPL", days=30, currency="usd"):
    """Fetch historical stock data and compute indicators."""
    try:
        # --- Date range ---
        end = datetime.today().date()
        start = end - timedelta(days=days)

        # --- Fetch from Yahoo Finance ---
        df = yf.download(
            ticker,
            start=start,
            end=end + timedelta(days=1),
            progress=False,
            auto_adjust=True
        )
        logging.info(f"Fetched {ticker}: {len(df)} rows from {start} to {end}")

        if df.empty:
            logging.warning(f"No data returned for ticker {ticker}")
            return pd.DataFrame(columns=["timestamp", "price", "MA7", "MA30", "daily_change", "volatility"])

        # --- Flatten MultiIndex columns (if any) ---
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = ["_".join(col).strip() if isinstance(col, tuple) else col for col in df.columns]

        df.reset_index(inplace=True)

        # --- Identify Close column ---
        close_candidates = [c for c in df.columns if "Close" in c]
        if not close_candidates:
            logging.warning(f"No 'Close' column found for {ticker}")
            return pd.DataFrame(columns=["timestamp", "price", "MA7", "MA30", "daily_change", "volatility"])

        close_col = close_candidates[0]

        # --- Keep only timestamp + price ---
        df = df[['Date', close_col]].rename(columns={'Date': 'timestamp', close_col: 'price'})

        # --- Convert to target currency ---
        fx_rate = get_fx_rate(currency)
        df["price"] = df["price"] * fx_rate

        # --- Calculate technical indicators ---
        df["MA7"] = df["price"].rolling(7).mean()
        df["MA30"] = df["price"].rolling(30).mean()
        df["daily_change"] = df["price"].pct_change() * 100
        df["volatility"] = df["price"].rolling(7).std()

        # Drop rows with NaN MAs
        df = df.dropna(subset=["MA7"]).reset_index(drop=True)

        # --- Log sample for debugging ---
        logging.info(f"Processed {ticker} rows: {len(df)}\nSample:\n{df.head()}")

        return df

    except Exception as e:
        logging.error(f"Error fetching/processing stock data for {ticker}: {e}")
        return pd.DataFrame(columns=["timestamp", "price", "MA7", "MA30", "daily_change", "volatility"])
