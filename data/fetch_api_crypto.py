import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import logging
import os
import json
import time
from requests.exceptions import RequestException

# --- Logging setup ---
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")

# --- Load config ---
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "config.json")
with open(config_path) as f:
    config = json.load(f)

COIN_MAP = config.get("coin_map", {})
if not COIN_MAP:
    logging.warning("⚠️ COIN_MAP is empty! Make sure your config.json has 'coin_map' defined.")


# ================================
# 🌐 Helper: Safe request with retry/backoff
# ================================
def safe_request(url, params=None, retries=5, base_delay=2):
    """Retry GET request with exponential backoff on 429 or network error."""
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 429:
                wait = base_delay * (2 ** attempt)
                logging.warning(f"429 Too Many Requests -> retrying in {wait}s...")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp
        except RequestException as e:
            wait = base_delay * (2 ** attempt)
            logging.warning(f"Request failed (attempt {attempt + 1}/{retries}): {e}. Retrying in {wait}s...")
            time.sleep(wait)
    logging.error(f"All retries failed for URL: {url}")
    return None


# ================================
# 🌐 FX RATE FETCHER
# ================================
@st.cache_data(ttl=3600)
def get_fx_rate(currency: str):
    if currency.lower() == "usd":
        return 1.0
    try:
        url = "https://open.er-api.com/v6/latest/USD"
        resp = safe_request(url)
        if not resp:
            raise Exception("No response from FX API")
        data = resp.json()
        rate = data.get("rates", {}).get(currency.upper(), 1.0)
        logging.info(f"get_fx_rate: USD -> {currency.upper()} = {rate}")
        return rate
    except Exception as e:
        logging.error(f"Failed to fetch FX rate for {currency}, default 1.0: {e}")
        return 1.0


# ================================
# 📈 CRYPTO DATA FETCHER
# ================================
def fetch_crypto_data(symbol, days, currency):
    symbol_upper = symbol.upper()
    coin_id = COIN_MAP.get(symbol_upper, symbol.lower())
    logging.info(f"Resolved coin_id: {coin_id}")

    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": currency.lower(), "days": days}
    
    wait_time = 2
    max_retries = 5

    for attempt in range(max_retries):
        try:
            resp = requests.get(url, params=params, timeout=10)
            
            if resp.status_code == 429:
                logging.warning(f"429 Too Many Requests -> retrying in {wait_time}s...")
                time.sleep(wait_time)
                wait_time *= 2
                continue

            resp.raise_for_status()
            data = resp.json().get("prices", [])
            if not data:
                logging.warning(f"No prices returned for {symbol}")
                return pd.DataFrame(columns=["timestamp", "price", "MA7", "MA30", "daily_change", "volatility"])

            df = pd.DataFrame(data, columns=["timestamp", "price"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            if currency.lower() != "usd":
                fx_rate = get_fx_rate(currency)
                df["price"] *= fx_rate

            df["MA7"] = df["price"].rolling(7, min_periods=1).mean()
            df["MA30"] = df["price"].rolling(30, min_periods=1).mean()
            df["daily_change"] = df["price"].pct_change() * 100
            df["volatility"] = df["price"].rolling(7, min_periods=1).std()

            logging.info(f"✅ Fetched {len(df)} rows for {symbol}")
            return df.reset_index(drop=True)

        except requests.RequestException as e:
            logging.error(f"Attempt {attempt+1} failed for {symbol}: {e}")
            time.sleep(wait_time)
            wait_time *= 2

    logging.error(f"Failed to fetch crypto data for {symbol} ({coin_id}) after {max_retries} retries.")
    return pd.DataFrame(columns=["timestamp", "price", "MA7", "MA30", "daily_change", "volatility"])



# ================================
# 📊 SIMULATE CRYPTO INVESTMENT
# ================================
@st.cache_data(ttl=3600)
def simulate_crypto_investment_curve(symbol, invest_date, amount, currency):
    """Return portfolio evolution from invest_date until today."""
    today = datetime.today().date()
    invest_dt = invest_date.date() if isinstance(invest_date, datetime) else invest_date
    days = (today - invest_dt).days
    if days <= 0:
        logging.warning("Investment date is today or in the future; cannot simulate.")
        return pd.DataFrame(columns=["timestamp","price","portfolio_value"])

    df = fetch_crypto_data(symbol, days, currency)
    if df.empty:
        logging.warning(f"No data for {symbol}")
        return pd.DataFrame(columns=["timestamp","price","portfolio_value"])

    # Ensure timestamp is datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"])
    df = df[df["timestamp"].dt.date >= invest_dt]

    if df.empty:
        logging.warning(f"No data after {invest_dt} for {symbol}")
        return pd.DataFrame(columns=["timestamp","price","portfolio_value"])

    start_price = df["price"].iloc[0]
    df["portfolio_value"] = amount * (df["price"] / start_price)
    return df[["timestamp","price","portfolio_value"]]
