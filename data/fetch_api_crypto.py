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

import time
import requests

def fetch_crypto_data(coin_id=None, vs_currency=None, days=None, retries=3, delay=2):
    """
    Fetch historical cryptocurrency market data from CoinGecko API with retry logic.

    Args:
        coin_id (str, optional): Cryptocurrency ID (e.g., 'bitcoin', 'ethereum').
                                 Defaults to 'bitcoin' if None.
        vs_currency (str, optional): Target currency (e.g., 'usd', 'eur').
                                     Defaults to 'usd' if None.
        days (int, optional): Number of past days to retrieve. Defaults to 30.
        retries (int, optional): Number of attempts if API call fails. Defaults to 3.
        delay (int, optional): Initial delay in seconds between retries, doubles on rate-limit. Defaults to 2.

    Returns:
        pd.DataFrame: DataFrame with columns ["timestamp", "price"]. Empty if fetch fails.

    Notes:
        - Handles HTTP errors, network issues, and rate-limiting (HTTP 429) gracefully.
        - Timestamps are converted to pandas datetime objects.
    """
    coin_id = coin_id or "bitcoin"
    vs_currency = vs_currency or "usd"
    days = days or 30

    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": vs_currency, "days": days}

    for attempt in range(retries):
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
                logging.warning(f"Rate limited for {coin_id}, retrying in {delay}s...")
                time.sleep(delay)
                delay *= 2
            else:
                logging.error(f"HTTP error for {coin_id}: {e}")
                return pd.DataFrame(columns=["timestamp", "price"])
        except requests.exceptions.RequestException as e:
            logging.error(f"Network/API error for {coin_id}: {e}")
            time.sleep(delay)
            delay *= 2

    logging.error(f"Failed to fetch data for {coin_id} after {retries} retries.")
    return pd.DataFrame(columns=["timestamp", "price"])
