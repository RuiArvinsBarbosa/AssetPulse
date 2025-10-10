import requests
import pandas as pd
import os
import json

# --- Load config once ---
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "config.json")
with open(config_path) as f:
    config = json.load(f)

def fetch_crypto_data(coin_id=None, vs_currency=None, days=None):
    """
    Fetch historical market data from CoinGecko.

    Parameters:
        coin_id (str): cryptocurrency ID (e.g., 'bitcoin')
        vs_currency (str): currency to convert to (e.g., 'usd')
        days (int): number of past days to fetch

    Returns:
        pd.DataFrame: timestamp, price
    """
    # Use config defaults if parameters not provided
    coin_id = coin_id or config["coins"][0]
    vs_currency = vs_currency or config.get("vs_currency", "usd")
    days = days or config.get("days", 30)

    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": vs_currency, "days": days}

    response = requests.get(url, params=params)
    response.raise_for_status()  # Raise error if request fails

    data = response.json()
    prices = data.get("prices", [])

    # Convert to DataFrame
    df = pd.DataFrame(prices, columns=["timestamp", "price"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

    return df
