\# AssetPulse

!\[Python](https://img.shields.io/badge/Python-3.11-blue)
!\[Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-orange)
!\[License](https://img.shields.io/badge/License-MIT-green)

\*\*Real-time crypto \& financial dashboard built with Python, Streamlit, and Plotly.\*\*

---

\## 🚀 Features

\- Fetch live cryptocurrency and stock data  
\- Candlestick charts with moving averages  
\- Portfolio simulation (planned)  
\- Export data to CSV/Excel (planned)  

---

\## 🛠 Tech Stack

\- \*\*Backend \& Data:\*\* Python, Pandas, NumPy  
\- \*\*Frontend:\*\* Streamlit  
\- \*\*Visualization:\*\* Plotly  
\- \*\*Data Sources:\*\* Yahoo Finance API (stocks), CoinGecko API (crypto)  

---

\## ⚙️ Configuration

All environment settings are stored in `config/config.json`. You can adjust assets, currencies, historical range, and PostgreSQL credentials.

```json

{
&nbsp;   "coins": \["bitcoin", "ethereum", "litecoin"],
&nbsp;   "stocks": \["AAPL", "MSFT", "GOOGL"],
&nbsp;   "vs\_currency": "usd",
&nbsp;   "currencies": \["usd", "eur", "gbp"],
&nbsp;   "days": 30,
&nbsp;   "postgres": {
&nbsp;       "host": "localhost",
&nbsp;       "port": 5432,
&nbsp;       "database": "assetpulse",
&nbsp;       "user": "assetpulse",
&nbsp;       "password": "pass"
&nbsp;   }
}

```

Explanation:

coins – List of cryptocurrencies to fetch from CoinGecko

stocks – Stock ticker symbols to fetch from Yahoo Finance

vs_currency – Default currency for crypto prices

currencies – Available currencies to select in the dashboard

days – Number of past days of historical data to fetch

postgres – Database credentials for logging historical prices (optional)

💻 How to Run Locally

Clone the repository:

git clone https://github.com/yourusername/AssetPulse.git
cd AssetPulse


Create a virtual environment and install dependencies:

python -m venv venv


Activate the virtual environment:

# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate

pip install -r requirements.txt


Configure your config/config.json (see Configuration section above).

Run the Streamlit dashboard:

streamlit run app/dashboard.py


Open the URL shown in the terminal (usually http://localhost:8501
).