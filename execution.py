import requests
import json
import hmac
import hashlib
import time
import os
from typing import Dict, Any, Literal, Optional, Annotated
from dataclasses import dataclass
from contextlib import contextmanager
from config import API_KEY, API_SECRET, BASE_URL, TESTNET, SYMBOLS
from logger import logger
try:
    from telegram_alerts import send_alert
except ImportError:
    def send_alert(msg: str) -> None:
        logger.error(f"ALERT: {msg}")

# Type aliases (Python 3.14+ style)
APIResponse = Dict[str, Any]
Timestamp = Annotated[int, 'milliseconds']
ProductID = str
OrderStatus = Literal['filled', 'rejected', 'cancelled', 'timeout', 'open']

@dataclass
class APIError(Exception):
    status: int
    message: str
    response: Optional[Dict[str, Any]] = None

class ProductCache:
    def __init__(self):
        self.cache: Dict[str, ProductID] = {}
        self.ttl: Dict[str, float] = {}  # expiry timestamp

    def get(self, symbol: str, timeout: float = 300.0) -> Optional[ProductID]:
        now = time.time()
        if symbol in self.cache and now < self.ttl.get(symbol, 0):
            return self.cache[symbol]
        return None

    def set(self, symbol: str, product_id: ProductID, ttl: float = 300.0):
        self.cache[symbol] = product_id
        self.ttl[symbol] = time.time() + ttl

product_cache = ProductCache()

def generate_signature(method: str, path: str, body: str, timestamp: Timestamp) -> str:
    """Delta Exchange v2 HMAC-SHA256 signature."""
    if API_SECRET is None:
        raise ValueError("API_SECRET not configured")
    base_string = f"{timestamp}{method}{path}{body}"
    return hmac.new(
        API_SECRET.encode('utf-8'),
        base_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

def make_request(
    method: Literal['GET', 'POST'],
    path: str,
    payload: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    timeout: float = 10.0,
    retries: int = 3
) -> APIResponse:
    """Generic authenticated Delta API request with retries."""
    body = json.dumps(payload or {}, separators=(',', ':')) if payload else ''
    timestamp = int(time.time() * 1000)
    headers = {
        'api-key': API_KEY or '',
        'signature': generate_signature(method, path, body, timestamp),
        'Content-Type': 'application/json',
        'timestamp': str(timestamp)
    }
    
    for attempt in range(retries):
        try:
            if method == 'GET':
                resp = requests.get(BASE_URL + path, headers=headers if payload else None, params=params or payload, timeout=timeout)
            else:  # POST
                resp = requests.post(BASE_URL + path, headers=headers, json=payload, timeout=timeout)
            
            data = resp.json()
            if resp.status_code == 200 and data.get('success', False):
                return data
            else:
                raise APIError(resp.status_code, str(data), data)
        except APIError:
            raise
        except Exception as e:
            logger.warning(f"API {method} {path} attempt {attempt+1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    
    send_alert(f"API FAILED after {retries} retries: {method} {path}")
    raise APIError(0, f"Max retries exceeded for {method} {path}")

def get_product_id(symbol: str) -> Optional[ProductID]:
    """Fetch and cache product_id."""
    cached = product_cache.get(symbol)
    if cached:
        return cached
    
    try:
        params = {'symbol': symbol, 'type': 'perpetual'}
        resp = requests.get(f"{BASE_URL}/v2/products", params=params, timeout=5).json()
        if resp.get('success') and resp.get('result'):
            pid = resp['result'][0]['id']
            product_cache.set(symbol, pid)
            logger.debug(f"Cached product_id {pid} for {symbol}")
            return pid
    except Exception as e:
        logger.error(f"Product ID fetch error {symbol}: {e}")
    return None

def check_order_status(order_id: str, max_wait: int = 30) -> OrderStatus:
    """Poll order status."""
    payload = {"order_id": order_id}
    for _ in range(max_wait):
        try:
            data = make_request('POST', '/v2/orders/status', payload)
            status = data['result'].get('status', 'unknown')
            if status in ['filled', 'rejected', 'cancelled']:
                return status
            time.sleep(1)
        except Exception:
            pass
    return 'timeout'

def place_order(
    symbol: str,
    side: str,
    size: float,
    tp_price: Optional[float] = None,
    sl_price: Optional[float] = None
) -> Dict[str, Any]:
    product_id = get_product_id(symbol)
    if not product_id:
        return {'success': False, 'error': f'No product for {symbol}'}
    
    payload = {
        "product_id": product_id,
        "side": side.lower(),
        "size": size,
        "order_type": "market_order"
    }
    try:
        data = make_request('POST', '/v2/orders', payload)
        order_id = data['result']['order_id']
        status = check_order_status(order_id)
        logger.info(f"✅ Order {symbol} {side} {size} ID:{order_id} status:{status} TP:{tp_price} SL:{sl_price}")
        return {'success': True, 'order_id': order_id, 'status': status}
    except APIError as e:
        logger.error(f"❌ Order failed {symbol}: {e.message}")
        return {'success': False, 'error': str(e)}

def get_balance() -> float:
    """Fetch USDT available balance, fallback to CAPITAL."""
    try:
        data = make_request('POST', '/v2/wallet/balances', payload={})
        for asset in data.get('result', []):
            if asset.get('asset', '').upper() == 'USDT':
                balance = float(asset.get('available_balance', 0))
                logger.info(f"💰 USDT Balance: ${balance:.2f}")
                return balance
        logger.warning("No USDT balance")
    except Exception as e:
        logger.error(f"Balance error: {e}")
    
    fallback = float(os.getenv('CAPITAL', '200.0'))
    logger.info(f"Using fallback capital: ${fallback}")
    return fallback

def get_ticker_price(symbol: str) -> Optional[float]:
    """Get mark price (public endpoint)."""
    try:
        params = {'symbol': symbol}
        resp = requests.get(f"{BASE_URL}/v2/tickers", params=params, timeout=5).json()
        if resp.get('success') and resp.get('result'):
            price = float(resp['result'][0]['mark_price'])
            logger.debug(f"Mark price {symbol}: {price}")
            return price
    except Exception as e:
        logger.error(f"Price fetch {symbol} error: {e}")
    return None

def close_position(symbol: str, side: str, size: float) -> Dict[str, Any]:
    """Close with opposite market order."""
    product_id = get_product_id(symbol)
    if not product_id:
        return {'success': False, 'error': 'No product_id'}
    
    close_side = 'sell' if side.upper() == 'BUY' else 'buy'
    payload = {
        "product_id": product_id,
        "side": close_side,
        "size": size,
        "order_type": "market_order"
    }
    try:
        data = make_request('POST', '/v2/orders', payload)
        order_id = data['result']['order_id']
        status = check_order_status(order_id)
        logger.info(f"🔒 Closed {symbol} {close_side} {size:.4f} ID:{order_id} status:{status}")
        return {'success': True, 'order_id': order_id, 'status': status}
    except APIError as e:
        logger.error(f"Close {symbol} error: {e.message}")
        return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    print("🧪 Testing fixed API functions...")
    if not API_KEY or not API_SECRET:
        print("⚠️ Skip tests: API keys missing (check .env)")
    else:
        try:
            balance = get_balance()
            print(f"✅ Balance: ${balance:.2f}")
            
            price = get_ticker_price(SYMBOLS[0])  # Use first symbol from config
            print(f"✅ {SYMBOLS[0]} Price: {price}")
        except Exception as e:
            print(f"❌ Test error: {e}")
    print("Tests complete.")

