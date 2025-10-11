import requests
import pandas as pd
import logging
import time
import random

def fetch_crypto_data(coin_id=None, vs_currency=None, days=None, max_retries=5, initial_delay=2, max_delay=60):
    """
    Fetch historical cryptocurrency market data from CoinGecko API with robust retry logic.

    Args:
        coin_id (str, optional): Cryptocurrency ID (default 'bitcoin')
        vs_currency (str, optional): Target currency (default 'usd')
        days (int, optional): Number of past days (default 30)
        max_retries (int, optional): Maximum retry attempts (default 5)
        initial_delay (int, optional): Initial backoff in seconds (default 2)
        max_delay (int, optional): Maximum backoff delay (default 60)

    Returns:
        pd.DataFrame: DataFrame with ["timestamp", "price"]
    """
    coin_id = coin_id or "bitcoin"
    vs_currency = vs_currency or "usd"
    days = days or 30

    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": vs_currency, "days": days}
    delay = initial_delay

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
            logging.info(f"Fetched {len(df)} rows for {coin_id}")
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
