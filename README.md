# AssetPulse

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-orange)
![License](https://img.shields.io/badge/License-MIT-green)

**Real-time crypto & financial dashboard built with Python, Streamlit, and Plotly.**

---

## 🚀 Features

* Fetch live cryptocurrency and stock data
* Candlestick charts with moving averages
* Portfolio simulation 💰
* Export data to CSV/Excel (planned)

---

## 🛠 Tech Stack

* **Backend & Data:** Python, Pandas, NumPy
* **Frontend:** Streamlit
* **Visualization:** Plotly
* **Data Sources:** Yahoo Finance API (stocks), CoinGecko API (crypto)
* **Database (optional):** PostgreSQL for historical price logging

---

## ⚙️ Configuration

All environment settings are stored in `config/config.json`. You can adjust assets, currencies, historical range, and PostgreSQL credentials.

```json
{
    "coins": ["bitcoin", "ethereum", "litecoin"],
    "stocks": ["AAPL", "MSFT", "GOOGL"],
    "vs_currency": "usd",
    "currencies": ["usd", "eur", "gbp"],
    "days": 30,
    "postgres": {
        "host": "localhost",
        "port": 5432,
        "database": "assetpulse",
        "user": "assetpulse",
        "password": "pass"
    }
}
```

**Explanation:**

* **coins** – List of cryptocurrencies to fetch from CoinGecko
* **stocks** – Stock ticker symbols to fetch from Yahoo Finance
* **vs_currency** – Default currency for crypto prices
* **currencies** – Available currencies to select in the dashboard
* **days** – Number of past days of historical data to fetch
* **postgres** – Database credentials for logging historical prices (optional)

---

## 💻 How to Run Locally

1. Clone the repository:

```bash
git clone https://github.com/yourusername/AssetPulse.git
cd AssetPulse
```

2. Create a virtual environment and install dependencies:

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

4. Install requirements:

```bash
pip install -r requirements.txt
```

5. Configure your `config/config.json` (see Configuration section above).

6. Run the Streamlit dashboard:

```bash
streamlit run app/dashboard.py
```

7. Open the URL shown in the terminal (usually `http://localhost:8501`).

---

## 🌐 Deployment (Optional)

* The app is deployed online using **Render**.
* Live demo: [https://assetpulse.onrender.com](https://assetpulse.onrender.com)

---

## 🖼 Screenshots

*Example dashboard showing crypto prices, moving averages, and portfolio simulation.*

![Dashboard Screenshot](docs/screenshot.png)

---

## ⚡ Notes

* **Error Handling:** API rate limits and network errors are handled with retries and logging.
* **Caching:** Crypto data is cached for 10 minutes to reduce API calls.
* **Portfolio Simulator:** Allows you to simulate investment growth over selected asset's history.
