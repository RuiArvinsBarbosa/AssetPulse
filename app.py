import os
import json
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv

from data.table_users_crud import (
    insert_users_ft,
    fetch_user_seq_no,
    fetch_all_users,
    fetch_users_by_seq_no,
    update_users,
    delete_users,
)

# -------------------------------
# Load .env first
# -------------------------------
load_dotenv()  # Load .env secrets (PostgreSQL credentials, etc.)

CONFIG_PATH = "config/config.json"
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH) as f:
        config_json = json.load(f)
else:
    st.error("Missing configuration file: config/config.json")
    st.stop()

# Load defaults from config.json
defaults = config_json.get("defaults", {})
if "app_theme" not in st.session_state:
    st.session_state["app_theme"] = defaults.get("app_theme", "Light")
if "default_currency" not in st.session_state:
    st.session_state["default_currency"] = defaults.get("default_currency", "USD")
if "data_refresh_rate" not in st.session_state:
    st.session_state["data_refresh_rate"] = defaults.get("data_refresh_rate", 15)
if "enable_logging" not in st.session_state:
    st.session_state["enable_logging"] = defaults.get("enable_logging", True)


# ==========================================================
# 🌐 PAGE CONFIG
# ==========================================================
st.set_page_config(
    page_title="AssetPulse – Home",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------
# THEME SETTINGS
# -------------------------------
theme = st.session_state.get("app_theme")
if theme is None:
    theme = os.getenv("APP_THEME", "Light") # fallback to "Light" if not in .env
    st.session_state["app_theme"] = theme   # store in session_state for consistency

bg_color, text_color, btn_bg, btn_text = (
    ("#0E1117", "white", "#444", "white") if theme == "Dark" else ("white", "black", "#eee", "black")
)

st.markdown(f"""
    <style>
    .css-18e3th9, .css-1outpf7, .css-1d391kg {{
        background-color: {bg_color} !important;
        color: {text_color} !important;
    }}
    .stButton>button {{
        background-color: {btn_bg};
        color: {btn_text};
    }}
    </style>
""", unsafe_allow_html=True)

# ==========================================================
# 🏠 HOME PAGE CONTENT
# ==========================================================
st.title("💹 Welcome to AssetPulse")

st.markdown("""
### Intelligent Analytics for Crypto & Stocks  
Monitor real-time market trends, compare assets, and visualize historical performance — all in one place.
""")

st.divider()

# ==========================================================
# 🔑 LOGIN / REGISTRATION
# ==========================================================
current_username = st.session_state.get("current_username")
username_email = st.session_state.get("username_email")

def is_valid_email(email: str) -> bool:
    """Basic email validation."""
    email = email.strip()
    if " " in email or email.count("@") != 1:
        return False
    local, domain = email.split("@")
    if not local or not domain or "." not in domain:
        return False
    return True

def username_exists(username: str, email: str) -> bool:
    username = username.strip()
    email = email.strip().lower()
    try:
        for u in fetch_all_users():
            db_username = u["username"].strip()
            db_email    = u["email"].strip().lower()
            if db_username == username and db_email == email:
                return True
        return False
    except Exception as e:
        st.error(f"Error checking username in DB: {e}")
        return False

# ==========================================================
# 🧩 LOGIN UI
# ==========================================================
if not current_username or not username_email:
    st.subheader("👤 Login / Create your account")
    nickname_input = st.text_input("Enter your nickname", "")
    email_input    = st.text_input("Enter your e-mail", "")

    if st.button("Login"):
        nickname = nickname_input.strip()
        email = email_input.strip()

        if not nickname:
            st.warning("Please enter a nickname.")
        elif not email:
            st.warning("Please enter your e-mail.")
        elif not is_valid_email(email):
            st.warning("Invalid e-mail format. Please enter a valid e-mail address.")
        else:
            if username_exists(nickname, email):
                st.session_state["current_username"] = nickname
                st.session_state["username_email"]   = email
                user_seq_no = fetch_user_seq_no(nickname, email)
                st.session_state["user_seq_no"] = user_seq_no
                st.success(f"Welcome back, {nickname}! Your account number is {user_seq_no}.")
            else:
                insert_users_ft(nickname, email)
                st.session_state["current_username"] = nickname
                st.session_state["username_email"]   = email
                user_seq_no = fetch_user_seq_no(nickname, email)
                st.session_state["user_seq_no"] = user_seq_no
                st.success(f"Welcome, {nickname}! Your account number is {user_seq_no}.")

# ==========================================================
# 🧾 SHOW USER + LOGOUT BUTTON
# ==========================================================
current_username = st.session_state.get("current_username")
username_email   = st.session_state.get("username_email")

if current_username and username_email:
    col1, col2 = st.columns([4, 1])
    with col1:
        st.info(f"**Logged in as:** {current_username} ({username_email})")
    with col2:
        if st.button("Logout"):
            st.session_state["current_username"] = None
            st.session_state["username_email"]   = None
            st.success("You have been logged out.")
