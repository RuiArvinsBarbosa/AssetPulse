import requests
import pandas as pd
import logging
import time
import random
from datetime import datetime, timedelta

# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

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

def fetch_crypto_data(coin_id="bitcoin", days=30, currency="usd"):
    """
    Fetch historical cryptocurrency data, convert to target currency,
    and calculate indicators.
    """
    coin_id = coin_id.lower()
    currency = currency.lower()
    end = datetime.today().date()
    start = end - timedelta(days=days)

    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": currency, "days": days}

    try:
        # --- Fetch data from CoinGecko ---
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        prices = data.get("prices", [])
        if not prices:
            logging.warning(f"No price data returned for {coin_id}")
            return pd.DataFrame(columns=["timestamp", "price", "MA7", "MA30", "daily_change", "volatility"])

        df = pd.DataFrame(prices, columns=["timestamp", "price"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

        # --- Convert FX if needed ---
        if currency != "usd":
            fx = get_fx_rate(currency)
            df["price"] = df["price"] * fx

        # --- Indicators ---
        df["MA7"] = df["price"].rolling(7).mean()
        df["MA30"] = df["price"].rolling(30).mean()
        df["daily_change"] = df["price"].pct_change() * 100
        df["volatility"] = df["price"].rolling(7).std()

        # Drop rows with NaN in MA7
        df = df.dropna(subset=["MA7"])

        logging.info(f"Fetched {coin_id}: {len(df)} rows from {start} to {end}")
        return df

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch crypto data for {coin_id}: {e}")
        return pd.DataFrame(columns=["timestamp", "price", "MA7", "MA30", "daily_change", "volatility"])
