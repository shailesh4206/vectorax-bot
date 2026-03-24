import requests
import json
import hmac
import hashlib
import time
from config import API_KEY, API_SECRET, BASE_URL, TESTNET
from logger import logger

def signature(payload):
    message = json.dumps(payload, separators=(',', ':'))
    return hmac.new(
        API_SECRET.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()

def get_product_id(symbol: str) -> str | None:
   """Fetch product_id for symbol from Delta API."""

    try:
        url = f\"{BASE_URL}/v2/products\"
        params = {\"symbol\": symbol, \"type\": \"perpetual\"}
        resp = requests.get(url, params=params)
        data = resp.json()
        if data.get('success') and data['result']:
            return data['result'][0]['id']
        logger.warning(f\"No product_id for {symbol}\")
        return None
    except Exception as e:
        logger.error(f\"Product ID fetch error {symbol}: {e}\")
        return None

def place_order(symbol: str, side: str, size: float, tp_price: float = None, sl_price: float = None) -> dict:
    \"\"\"
    Place market order with optional TP/SL (bracket if supported).
    Returns {'success': bool, 'order_id': str, 'status': str}
    \"\"\"
    product_id = get_product_id(symbol)
    if not product_id:
        return {'success': False, 'error': f'No product_id for {symbol}'}
    
    for attempt in range(3):
        payload = {
            \"product_id\": product_id,
            \"side\": side.lower(),
            \"size\": size,
            \"order_type\": \"market_order\",
            \"timestamp\": int(time.time() * 1000)
        }
        
        # Delta doesn't support direct TP/SL in payload; handle separately
        # For now, place market, log TP/SL for manual
        
        headers = {
            \"api-key\": API_KEY,
            \"signature\": signature(payload),
            \"Content-Type\": \"application/json\",
            \"timestamp\": str(payload[\"timestamp\"])
        }
        
        try:
            response = requests.post(
                BASE_URL + \"/v2/orders\",
                headers=headers,
                json=payload,
                timeout=10
            )
            data = response.json()
            
            if response.status_code == 200 and data.get('success'):
                order_id = data['result']['order_id']
                logger.info(f\"Order placed: {symbol} {side} {size} ID:{order_id} TP:{tp_price} SL:{sl_price}\")
                status = check_order_status(order_id)
                return {'success': True, 'order_id': order_id, 'status': status}
            else:
                logger.error(f\"Order failed attempt {attempt+1}: {data}\")
        except Exception as e:
            logger.error(f\"Order attempt {attempt+1} exception: {e}\")
        
        if attempt < 2:
            time.sleep(2 ** attempt)
    
    from telegram_alerts import send_alert\n    send_alert(f"❌ TRADE FAILED {symbol}: Failed after 3 attempts")\n    return {'success': False, 'error': 'Failed after 3 attempts'}

def check_order_status(order_id: str, max_wait: int = 30) -> str:
    \"\"\"Poll order status.\"\"\"

    payload = {\"order_id\": order_id}
    headers = {
        \"api-key\": API_KEY,
        \"signature\": signature(payload),
        \"Content-Type\": \"application/json\"
    }
    
    for _ in range(max_wait):
        try:
            resp = requests.post(
                BASE_URL + \"/v2/orders/status\",
                headers=headers,
                json=payload,
                timeout=5
            )
            data = resp.json()
            status = data['result']['status']
            if status in ['filled', 'rejected', 'cancelled']:
                return status
            time.sleep(1)
        except:
            pass
    return 'timeout'

def get_balance():
    \"\"\"Fetch USDT wallet balance/equity for small capital sizing.\"\"\"

    try:
        timestamp = int(time.time() * 1000)
        payload = {\"timestamp\": timestamp}
        headers = {
            \"api-key\": API_KEY,
            \"signature\": signature(payload),
            \"Content-Type\": \"application/json\"
        }
        resp = requests.post(f\"{BASE_URL}/v2/wallets\", headers=headers, json=payload, timeout=10)
        data = resp.json()
        if data.get('success'):
            for asset in data['result']:
                if asset['asset'].upper() == 'USDT':
                    equity = float(asset.get('equity', 0))
                    logger.info(f\"💰 Balance: ${equity:.2f} USDT (for ₹200 equiv sizing)\")
                    return equity
        logger.warning(\"No USDT balance found\")
        return float(os.getenv(\"CAPITAL\", 200))  # Fallback
    except Exception as e:
        logger.error(f\"Balance fetch error: {e}\")
        return 0.0

def get_ticker_price(symbol: str) -> float | None:
    \"\"\"Get current mark price.\"\"\"

    try:
        url = f\"{BASE_URL}/v2/luidDepth?symbol={symbol}\"
        resp = requests.get(url, timeout=5)
        data = resp.json()
        if data.get('success') and data['result']:
            return float(data['result'][0]['mark_price'])
        return None
    except Exception as e:
        logger.error(f\"Price fetch {symbol} error: {e}\")
        return None

def close_position(symbol: str, side: str, size: float) -> dict:
    \"\"\"Close position w/ opposite market order.\"\"\"

    product_id = get_product_id(symbol)
    if not product_id:
        return {'success': False, 'error': 'No product_id'}
    
    close_side = 'sell' if side.upper() == 'BUY' else 'buy'
    timestamp = int(time.time() * 1000)
    payload = {
        \"product_id\": product_id,
        \"side\": close_side,
        \"size\": size,
        \"order_type\": \"market_order\",
        \"timestamp\": timestamp
    }
    headers = {
        \"api-key\": API_KEY,
        \"signature\": signature(payload),
        \"Content-Type\": \"application/json\",
        \"timestamp\": str(timestamp)
    }
    try:
        resp = requests.post(f\"{BASE_URL}/v2/orders\", headers=headers, json=payload, timeout=10)
        data = resp.json()
        if resp.status_code == 200 and data.get('success'):
            logger.info(f\"🔒 Closed {symbol} {side} {size:.4f}\")
            tracker.close_position(symbol)
            return {'success': True}
        return {'success': False, 'error': str(data)}
    except Exception as e:
        logger.error(f\"Close {symbol} error: {e}\")
        return {'success': False, 'error': str(e)}

