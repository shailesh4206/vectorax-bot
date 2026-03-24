import os
import platform
from dotenv import load_dotenv

# Load .env file
import platform
if platform.system() == "Windows":
    os.system('chcp 65001 >nul 2>&1')

print("DEBUG: Loading .env file...")
dotenv_loaded = load_dotenv()

print(f"DEBUG: .env loaded: {'YES' if dotenv_loaded else 'NO'}")


# ===============================
# API KEYS
# ===============================
API_KEY = os.getenv("DELTA_API_KEY")
API_SECRET = os.getenv("DELTA_API_SECRET")


# ===============================
# EXCHANGE MODE
# ===============================
TESTNET = os.getenv("TESTNET", "true").strip().lower() == "true"

TESTNET_URL = "https://testnet-api.delta.exchange"
MAINNET_URL = "https://api.delta.exchange"

BASE_URL = TESTNET_URL if TESTNET else MAINNET_URL


# ===============================
# TRADING SETTINGS
# ===============================
if TESTNET:
    SYMBOLS = ["BTCUSD", "ETHUSD"]
else:
    SYMBOLS = [s.strip() for s in os.getenv(
        "SYMBOLS",
        "BTCUSD_PERP,ETHUSD_PERP"
    ).split(",")]

CAPITAL = float(os.getenv("CAPITAL", "200"))  # ₹200 small capital default

RISK_PERCENT = 0.01  # 1% risk per trade
SL_PERCENT = 0.01  # 1% stoploss
TP_PERCENT = 0.025  # 2.5% target
RR_RATIO = 2.5  # Risk-Reward 2.5

MAX_TRADES = int(os.getenv("MAX_TRADES", "3"))  # Maximum 3 open positions


# ===============================
# TELEGRAM SETTINGS
# ===============================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


# ===============================
# LOGGING SETTINGS
# ===============================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


# ===============================
# REPORTING
# ===============================
SUMMARY_FILE_PATH = os.getenv("SUMMARY_FILE_PATH", "summary.txt")


# ===============================
# DEBUG STATUS OUTPUT
# ===============================
print(f"DEBUG: API KEY PRESENT: {'YES' if API_KEY else 'NO'}")
print(f"DEBUG: API SECRET PRESENT: {'YES' if API_SECRET else 'NO'}")
print(f"DEBUG: TELEGRAM TOKEN PRESENT: {'YES' if TELEGRAM_TOKEN else 'NO'}")
print(f"DEBUG: TELEGRAM CHAT ID PRESENT: {'YES' if TELEGRAM_CHAT_ID else 'NO'}")
print(f"DEBUG: TESTNET MODE: {TESTNET}")
print(f"DEBUG: BASE_URL: {BASE_URL}")
print(f"DEBUG: SYMBOLS: {SYMBOLS}")
print(f"DEBUG: SUMMARY_FILE_PATH: {SUMMARY_FILE_PATH}")
print(f"DEBUG: Risk: {RISK_PERCENT*100}% SL:{SL_PERCENT*100}% TP:{TP_PERCENT*100}% RR:{RR_RATIO}")


# ===============================
# REQUIRED VARIABLE CHECK
# ===============================
required_vars = [
    "DELTA_API_KEY",
    "DELTA_API_SECRET",
    "TELEGRAM_TOKEN",
    "TELEGRAM_CHAT_ID"
]

missing_vars = [
    var for var in required_vars
    if not os.getenv(var)
]

if missing_vars:
    raise ValueError(
        f"Missing required environment variables: {missing_vars}"
    )

print("SUCCESS: All environment variables loaded correctly")

