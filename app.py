import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime

# --- Streamlit page setup ---
st.set_page_config(page_title="AssetPulse - Crypto Tracker", layout="wide")
st.title("💹 AssetPulse - Live Crypto Price Tracker")

# --- Sidebar: User inputs ---
COINS = {
    "Bitcoin": "bitcoin",
    "Ethereum": "ethereum",
    "Solana": "solana"
}

asset_name = st.sidebar.selectbox("Select Crypto Asset", list(COINS.keys()))
asset = COINS[asset_name]

currency = st.sidebar.selectbox("Select Currency", ["usd", "eur"])
days = st.sidebar.slider("Days to show", min_value=1, max_value=90, value=30)

# --- Function to fetch crypto data from CoinGecko ---
@st.cache_data(ttl=60)  # cache for 1 minute to reduce API calls
def get_crypto_data(asset_id, currency, days):
    url = f"https://api.coingecko.com/api/v3/coins/{asset_id}/market_chart"
    params = {"vs_currency": currency, "days": days}
    response = requests.get(url, params=params)

    if response.status_code != 200:
        st.error(f"API request failed with status code {response.status_code}")
        return pd.DataFrame()

    data = response.json()
    if "prices" not in data:
        st.error(f"API did not return prices for {asset_name}. Response keys: {list(data.keys())}")
        return pd.DataFrame()

    df = pd.DataFrame(data["prices"], columns=["timestamp", "price"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df

# --- Fetch data ---
df = get_crypto_data(asset, currency, days)

if not df.empty:
    # --- Data science calculations ---
    df["MA7"] = df["price"].rolling(7).mean()
    df["MA30"] = df["price"].rolling(30).mean()
    df["daily_change"] = df["price"].pct_change() * 100

    # --- Plot price with moving averages ---
    fig_price = px.line(
        df,
        x="timestamp",
        y=["price", "MA7", "MA30"],
        labels={"value": f"Price ({currency.upper()})", "timestamp": "Date"},
        title=f"{asset_name} Price with 7 & 30 Day MA"
    )
    st.plotly_chart(fig_price, use_container_width=True)

    # --- Plot daily % change ---
    fig_change = px.bar(
        df,
        x="timestamp",
        y="daily_change",
        labels={"daily_change": "% Change", "timestamp": "Date"},
        title=f"{asset_name} Daily % Change"
    )
    st.plotly_chart(fig_change, use_container_width=True)

    # --- Optional: show raw data ---
    with st.expander("Show raw data"):
        st.dataframe(df)
else:
    st.warning("No data to display. Try changing the asset or the date range.")
