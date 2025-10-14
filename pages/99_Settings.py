import streamlit as st
import json
import os

# ==========================================================
# 🌐 PAGE CONFIG
# ==========================================================
st.set_page_config(page_title            = "AssetPulse – Settings",
                   layout                = "wide"                 ,
                   initial_sidebar_state = "expanded"             )

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

# --- User session check ---
current_user = st.session_state.get("current_user")
user_email   = st.session_state.get("user_email")

# --- Check login ---
if "current_username" not in st.session_state or "username_email" not in st.session_state:
    st.warning("You must log in before accessing this page.")
    
    # Optional: redirect to login page if you have one
    # st.experimental_set_query_params(page="login")

    st.stop()  # Stop the page from rendering further

# ==========================================================
# 🏠 PAGE HEADER
# ==========================================================
col_title, col_user = st.columns([8, 4])
col_title.title("⚙️ Settings")
col_user.markdown(
    f"**Logged in as:** {current_user} ({user_email})",
    unsafe_allow_html=True
)

st.markdown("Adjust your application preferences below.")

# ==========================================================
# 🔧 DEFAULT SETTINGS (fall back if session empty)
# ==========================================================
default_app_theme = st.session_state.get("app_theme", "Light")
default_currency  = st.session_state.get("default_currency", "USD")
default_refresh   = st.session_state.get("data_refresh_rate", 15)
default_logging   = st.session_state.get("enable_logging", True)

# ==========================================================
# --- General Settings ---
# ==========================================================
st.header("General Settings")
app_theme        = st.selectbox("App Theme", ["Light", "Dark"], index=["Light","Dark"].index(default_app_theme))
default_currency = st.selectbox("Default Currency", ["USD", "EUR", "GBP"], index=["USD","EUR","GBP"].index(default_currency))

# ==========================================================
# --- Advanced Settings ---
# ==========================================================
st.header("Advanced Settings")
data_refresh_rate = st.slider("Data Refresh Rate (minutes)", 1, 60, value=default_refresh)
enable_logging    = st.checkbox("Enable Logging", value=default_logging)

# ==========================================================
# --- Apply theme dynamically ---
# ==========================================================
if app_theme == "Dark":
    st.markdown(
        """
        <style>
        body { background-color: #0E1117; color: white; }
        .stButton>button { background-color: #444; color: white; }
        .stSlider>div>div>div>div { background-color: #222 !important; }
        .stSelectbox>div>div { background-color: #222 !important; color: white; }
        </style>
        """, unsafe_allow_html=True
    )
else:
    st.markdown(
        """
        <style>
        body { background-color: white; color: black; }
        .stButton>button { background-color: #eee; color: black; }
        </style>
        """, unsafe_allow_html=True
    )

# ==========================================================
# --- Save settings ---
# ==========================================================
def save_settings():
    st.session_state["app_theme"]        = app_theme
    st.session_state["default_currency"] = default_currency
    st.session_state["data_refresh_rate"]= data_refresh_rate
    st.session_state["enable_logging"]   = enable_logging

    # Optionally save to JSON for persistence
    config_dir = os.path.join(os.getcwd(), "config")
    os.makedirs(config_dir, exist_ok=True)
    config_path = os.path.join(config_dir, "user_settings.json")

    settings = {
        "app_theme"        : app_theme,
        "default_currency" : default_currency,
        "data_refresh_rate": data_refresh_rate,
        "enable_logging"   : enable_logging
    }

    with open(config_path, "w") as f:
        json.dump(settings, f, indent=4)

    st.success("Settings saved successfully!")
    st.json(settings)

st.button("Save Settings", on_click=save_settings)

# ==========================================================
# --- Show current settings ---
# ==========================================================
st.info(f"Current theme: **{app_theme}**, Default currency: **{default_currency}**, "
        f"Refresh Rate: **{data_refresh_rate} min**, Logging: **{enable_logging}**")