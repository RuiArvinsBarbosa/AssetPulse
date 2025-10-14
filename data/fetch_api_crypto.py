from datetime import datetime, date, timedelta
import requests
import pandas as pd
import logging
import os
import json

# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# --- Load config safely ---
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "config.json")

try:
    with open(CONFIG_PATH, "r") as f:
        CONFIG = json.load(f)
        logging.info(f"Loaded configuration from {CONFIG_PATH}")
except FileNotFoundError:
    logging.error(f"Config file not found at {CONFIG_PATH}")
    CONFIG = {}

COIN_MAP = CONFIG.get("coin_map", {})
if not COIN_MAP:
    logging.warning("⚠️ COIN_MAP is empty! Make sure your config/config.json has 'coin_map' defined.")

# --- FX ---
def get_fx_rate(currency: str):
    if currency.lower() == "usd":
        return 1.0
    try:
        url = "https://open.er-api.com/v6/latest/USD"
        response = requests.get(url, timeout=10)
        data = response.json()
        return data.get("rates", {}).get(currency.upper(), 1.0)
    except Exception as e:
        logging.error(f"Failed to fetch FX rate for {currency}, defaulting to 1.0: {e}")
        return 1.0

# --- Crypto fetch ---
def fetch_crypto_data(coin_id="bitcoin", days=30, currency="usd"):
    coin_id  = coin_id.lower()
    currency = currency.lower()
    end   = datetime.today().date()
    start = end - timedelta(days=days)
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": currency, "days": days}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        prices = response.json().get("prices", [])
        if not prices:
            return pd.DataFrame(columns=["timestamp", "price", "MA7", "MA30", "daily_change", "volatility"])
        df = pd.DataFrame(prices, columns=["timestamp", "price"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        if currency != "usd":
            fx = get_fx_rate(currency)
            df["price"] *= fx
        df["MA7"] = df["price"].rolling(7).mean()
        df["MA30"] = df["price"].rolling(30).mean()
        df["daily_change"] = df["price"].pct_change() * 100
        df["volatility"] = df["price"].rolling(7).std()
        df = df.dropna(subset=["MA7"])
        return df
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch crypto data for {coin_id}: {e}")
        return pd.DataFrame(columns=["timestamp", "price", "MA7", "MA30", "daily_change", "volatility"])

# --- Price on date ---
def get_crypto_price_on_date(symbol="BTC", date_value=None, currency="usd"):
    if date_value is None:
        date_value = datetime.today().date()
    coin_id = COIN_MAP.get(symbol.upper())
    if not coin_id:
        logging.error(f"Symbol '{symbol}' not in COIN_MAP")
        return None
    date_str = date_value.strftime("%d-%m-%Y")
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/history"
    params = {"date": date_str, "localization": "false"}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        price = response.json()["market_data"]["current_price"].get(currency.lower())
        return price
    except Exception as e:
        logging.error(f"Failed to fetch price for {symbol} on {date_str}: {e}")
        return None

# --- Simulate investment ---
def simulate_investment(symbol="BTC", invest_date=None, amount=1000.0, currency="usd"):
    if invest_date is None:
        invest_date = datetime(2023, 1, 1)
    invest_price = get_crypto_price_on_date(symbol, invest_date, currency)
    current_price = get_crypto_price_on_date(symbol, datetime.today().date(), currency)
    if invest_price is None or current_price is None:
        return None
    return amount * current_price / invest_price

def get_valid_coin_id(symbol: str):
    symbol = symbol.upper()
    return COIN_MAP.get(symbol, symbol.lower())

def get_crypto_timeseries(symbol="BTC", days=365, currency="usd"):
    coin_id = get_valid_coin_id(symbol)
    return fetch_crypto_data(coin_id=coin_id, days=days, currency=currency)

def simulate_investment_curve(symbol="BTC", invest_date=None, amount=1000.0, currency="usd"):
    if invest_date is None:
        invest_date = datetime(2023, 1, 1)
    today = datetime.today().date()
    invest_date_only = invest_date.date() if isinstance(invest_date, datetime) else invest_date
    days = (today - invest_date_only).days
    if days <= 0:
        return pd.DataFrame(columns=["timestamp", "portfolio_value"])
    coin_id = get_valid_coin_id(symbol)
    df = fetch_crypto_data(coin_id=coin_id, days=days, currency=currency)
    if df.empty:
        return pd.DataFrame(columns=["timestamp", "portfolio_value"])
    df = df[df["timestamp"].dt.date >= invest_date_only]
    if df.empty:
        return pd.DataFrame(columns=["timestamp", "portfolio_value"])
    start_price = df["price"].iloc[0]
    df["portfolio_value"] = amount * (df["price"] / start_price)
    return df
