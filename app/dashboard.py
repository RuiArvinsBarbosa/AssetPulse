import sys
import os
import json
import streamlit as st
import pandas as pd
import plotly.express as px

# --- Ensure root folder is in sys.path so modules work ---
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- Import fetch function ---
from data.fetch_data import fetch_crypto_data

# --- Load config ---
with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "config.json")) as f:
    config = json.load(f)

# --- Streamlit UI ---
st.title("AssetPulse – Crypto Dashboard")

# Select cryptocurrency from config
coin = st.selectbox("Select cryptocurrency", config["coins"])

# Fetch data from CoinGecko
df = fetch_crypto_data(
    coin_id=coin,
    vs_currency=config.get("vs_currency", "usd"),
    days=config.get("days", 30)
)

# --- Analysis: 7-day moving average ---
df["MA7"] = df["price"].rolling(7).mean()

# --- Streamlit chart ---
fig = px.line(
    df,
    x="timestamp",
    y=["price", "MA7"],
    title=f"{coin.capitalize()} Price & 7-Day MA",
    labels={"value": "Price (USD)", "timestamp": "Date"}
)
st.plotly_chart(fig, use_container_width=True)

# --- Optional: Show raw data ---
if st.checkbox("Show raw data"):
    st.dataframe(df)
