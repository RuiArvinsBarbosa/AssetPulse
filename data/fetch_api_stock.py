import streamlit as st
import requests
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import logging
import os
import json
import time

# ==========================================================
# 🧠 LOGGING SETUP
# ==========================================================
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")

# ==========================================================
# ⚙️ LOAD CONFIG
# ==========================================================
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "config.json")
with open(config_path) as f:
    config = json.load(f)

# ==========================================================
# 🌐 FX RATE FETCHER
# ==========================================================
@st.cache_data(ttl=3600)
def get_fx_rate(currency: str):
    """Return USD->currency exchange rate (1.0 if USD)."""
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
        logging.error(f"Failed to fetch FX rate for {currency}, defaulting to 1.0: {e}")
        return 1.0

# ==========================================================
# 💹 STOCK DATA FETCHER (Yahoo Finance)
# ==========================================================
@st.cache_data(ttl=3600)
def fetch_stock_data(ticker, days, currency):
    """Fetch historical stock data from Yahoo Finance with retry and rate-limit handling."""
    end = datetime.today().date()
    start = end - timedelta(days=days)
    max_retries = 5
    wait_time = 2

    for attempt in range(max_retries):
        try:
            df = yf.download(
                ticker, start=start, end=end + timedelta(days=1),
                progress=False, auto_adjust=True
            )

            if df.empty:
                logging.warning(f"No data returned for {ticker} (attempt {attempt+1})")
                time.sleep(wait_time)
                continue

            # Flatten MultiIndex if exists
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = ["_".join(col).strip() if isinstance(col, tuple) else col for col in df.columns]

            df.reset_index(inplace=True)
            close_col = next((c for c in df.columns if "Close" in c), None)
            if not close_col:
                logging.warning(f"No Close column for {ticker}")
                return pd.DataFrame(columns=["timestamp", "price", "MA7", "MA30", "daily_change", "volatility"])

            df = df[["Date", close_col]].rename(columns={"Date": "timestamp", close_col: "price"})
            df["timestamp"] = pd.to_datetime(df["timestamp"])

            if not df.empty and currency.lower() != "usd":
                fx_rate = get_fx_rate(currency)
                df["price"] *= fx_rate

            # Add indicators
            df["MA7"] = df["price"].rolling(7, min_periods=1).mean()
            df["MA30"] = df["price"].rolling(30, min_periods=1).mean()
            df["daily_change"] = df["price"].pct_change() * 100
            df["volatility"] = df["price"].rolling(7, min_periods=1).std()

            logging.info(f"✅ Fetched {len(df)} rows for {ticker} from {start} to {end}")
            return df.reset_index(drop=True)

        except yf.shared._exceptions.YFRateLimitError:
            logging.warning(f"⚠️ Rate limited by Yahoo Finance on attempt {attempt+1}. Retrying in {wait_time}s...")
            time.sleep(wait_time)
            wait_time *= 2  # Exponential backoff
        except Exception as e:
            logging.error(f"Error fetching stock data for {ticker} (attempt {attempt+1}): {e}")
            time.sleep(wait_time)
            wait_time *= 2

    logging.error(f"❌ Failed to fetch stock data for {ticker} after {max_retries} attempts.")
    return pd.DataFrame(columns=["timestamp", "price", "MA7", "MA30", "daily_change", "volatility"])

# ==========================================================
# 💰 SIMULATE STOCK INVESTMENT CURVE
# ==========================================================
@st.cache_data(ttl=3600)
def simulate_stock_investment_curve(ticker, invest_date, amount, currency):
    """Simulate portfolio evolution from invest_date until today."""
    today = datetime.today().date()
    invest_dt = invest_date.date() if isinstance(invest_date, datetime) else invest_date
    days = (today - invest_dt).days

    if days <= 0:
        logging.warning("Investment date is today or in the future; cannot simulate.")
        return pd.DataFrame(columns=["timestamp", "price", "portfolio_value"])

    df = fetch_stock_data(ticker, days, currency)
    df = df[df["timestamp"].dt.date >= invest_dt].copy()
    if df.empty:
        logging.warning(f"No data after {invest_dt} for {ticker}")
        return pd.DataFrame(columns=["timestamp", "price", "portfolio_value"])

    start_price = df["price"].iloc[0]
    df["portfolio_value"] = amount * (df["price"] / start_price)
    return df[["timestamp", "price", "portfolio_value"]]
