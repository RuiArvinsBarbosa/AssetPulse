# AssetPulse

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-orange)
![License](https://img.shields.io/badge/License-MIT-green)

**Real-time crypto & financial dashboard built with Python, Streamlit, and Plotly.**

---

## 🚀 Features

* Fetch live cryptocurrency and stock market data
* Interactive candlestick charts with moving averages (7-day, 30-day)
* Portfolio simulator – track your investments 💰
* Export portfolio data to CSV/Excel (planned)
* Configurable dashboard for coins, stocks, currencies, and historical range
* Optional PostgreSQL logging for historical price tracking
* Automatic error handling and API rate limit retries
* Customizable defaults: theme, currency, data refresh rate, logging
* Expanded asset coverage: 11 cryptocurrencies and 12 stocks

---

## 🛠 Tech Stack

* **Backend & Data:** Python, Pandas, NumPy
* **Frontend:** Streamlit
* **Visualization:** Plotly
* **Data Sources:** Yahoo Finance API (stocks), CoinGecko API (crypto)
* **Database:** PostgreSQL for optional historical logging

---

## ⚙️ Configuration

All environment settings are stored in `config/config.json`. You can adjust assets, currencies, historical range, and PostgreSQL credentials.

```json
{
    "coins": [
        "avalanche-2", "binancecoin", "bitcoin", "cardano", "dogecoin",
        "ethereum", "litecoin", "matic-network", "polkadot", "ripple", "solana"
    ],
    "stocks": [
        "AAPL", "AMD", "AMZN", "GOOGL", "IBM", "INTC", "META", "MSFT",
        "NFLX", "NVDA", "ORCL", "TSLA"
    ],
    "vs_currency": "usd",
    "currencies": ["usd", "eur", "gbp"],
    "days": 30,
    "defaults": {
        "app_theme": "Light",
        "default_currency": "USD",
        "data_refresh_rate": 15,
        "enable_logging": true
    },
    "coin_map": {
        "ADA": "cardano",
        "AVAX": "avalanche-2",
        "BNB": "binancecoin",
        "BTC": "bitcoin",
        "DOGE": "dogecoin",
        "DOT": "polkadot",
        "ETH": "ethereum",
        "LTC": "litecoin",
        "MATIC": "matic-network",
        "SOL": "solana",
        "XRP": "ripple"
    }
}
```

**Explanation of fields:**

* **coins** – Cryptocurrencies to fetch from CoinGecko
* **stocks** – Stock ticker symbols to fetch from Yahoo Finance
* **currencies** – Dashboard display currencies
* **days** – Historical data range (days)
* **defaults** – Dashboard default settings:

  * **app_theme** – Light or Dark theme
  * **default_currency** – Currency displayed on the dashboard
  * **data_refresh_rate** – Refresh interval in minutes
  * **enable_logging** – Enable or disable historical logging
* **postgres** – PostgreSQL credentials (optional)
* **coin_map** – Maps short symbols to CoinGecko IDs

---

## 🖥️ Deployment Modes

AssetPulse supports **dual deployment modes** for flexible usage:

1. **Local Docker PostgreSQL**

   * Run a local PostgreSQL database using Docker
   * Ideal for development, testing, or offline use
   * Fully compatible with all dashboard features

2. **Supabase-hosted PostgreSQL**

   * Connect to a cloud PostgreSQL database via Supabase
   * Ideal for production or sharing the dashboard online
   * Automatically accessible from anywhere, no local setup required

**How to switch:**
Simply update your `config/config.json` with the correct PostgreSQL credentials. The app automatically detects the database and logs historical data accordingly.

---

## 💻 How to Run Locally

1. Clone the repository:

```bash
git clone https://github.com/yourusername/AssetPulse.git
cd AssetPulse
```

2. Create a virtual environment:

```bash
python -m venv venv
```

3. Activate the virtual environment:

```bash
# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Configure `config/config.json` (see Configuration section above).

6. Run the Streamlit dashboard:

```bash
streamlit run dashboard.py
```

7. Open the URL shown in the terminal (usually `http://localhost:8501`).

---

## 🌐 Deployment

* Hosted online using **Render**
* Live demo: [https://assetpulse.onrender.com](https://assetpulse.onrender.com)

---

## 🖼 Screenshots

*Example dashboard showing crypto prices, moving averages, and portfolio simulation.*

![Dashboard Screenshot](docs/screenshot.png)

---

## ⚡ Notes

* **Error Handling:** API rate limits and network issues are managed with retries & logging
* **Caching:** Crypto data cached for 10 minutes to reduce API calls
* **Portfolio Simulator:** Tracks hypothetical investments over historical data
* **Custom Defaults:** Theme, currency, refresh rate, and logging can be configured
* **Expanded Asset Coverage:** 11 cryptocurrencies, 12 stocks
* **Stable Version:** Fully-configurable and ready for deployment
