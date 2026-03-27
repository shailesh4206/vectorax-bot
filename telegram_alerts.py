import requests
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
from logger import logger

def send_alert(message: str) -> bool:
    """
    Send Telegram alert.
    Returns True if successful.
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, data=payload, timeout=10)
        if response.status_code == 200:
            logger.info("Telegram alert sent ✅")
            return True
        else:
            logger.error(f"Telegram failed {response.status_code}: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Telegram error: {e}")
        return False

# Test
if __name__ == "__main__":
    send_alert("Vectorax Trading Bot connected successfully 🚀")

