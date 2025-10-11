import requests
import pandas   as pd
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


def fetch_stock_data(ticker="AAPL", days=30):
    """
    Fetch historical stock data from Yahoo Finance, calculate technical indicators,
    and handle errors gracefully.

    Args:
        ticker (str, optional): Stock ticker symbol (e.g., 'AAPL', 'GOOGL').
                                Defaults to 'AAPL'.
        days (int, optional): Number of past days of data to retrieve. Defaults to 30.

    Returns:
        pd.DataFrame: Cleaned DataFrame containing the following columns:
            - 'timestamp': Date of the data point
            - 'price': Closing price
            - 'MA7': 7-day moving average
            - 'MA30': 30-day moving average
            - 'daily_change': Daily percentage change
            - 'volatility': 7-day rolling standard deviation of price
        Returns an empty DataFrame with the same columns if data is missing
        or an error occurs.

    Notes:
        - Flattens MultiIndex columns returned by yfinance if necessary.
        - Drops rows where moving averages are NaN.
        - Uses auto-adjusted prices for accurate calculations.
    """
    try:
        # --- Use only date, no time ---
        end   = datetime.today().date()
        start = end - timedelta(days=days)

        # Fetch data
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

        logging.info(f"Columns after flatten: {df.columns}, using close column: {close_col}")

        # Keep only timestamp + price
        df = df[['Date', close_col]].rename(columns={'Date': 'timestamp', close_col: 'price'})

        # --- Calculate indicators ---
        df["MA7"]           = df["price"].rolling(7).mean()
        df["MA30"]          = df["price"].rolling(30).mean()
        df["daily_change"]  = df["price"].pct_change() * 100
        df["volatility"]    = df["price"].rolling(7).std()

        # Drop rows where moving averages are NaN
        df = df.dropna(subset=["MA7"])

        logging.info(f"Processed data rows: {len(df)}")
        return df

    except Exception as e:
        logging.error(f"Error fetching/processing stock data for {ticker}: {e}")
        return pd.DataFrame(columns=["timestamp", "price", "MA7", "MA30", "daily_change", "volatility"])
