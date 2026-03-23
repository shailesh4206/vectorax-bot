import time  
import pandas as pd  
import requests  
from config import BASE_URL  
from logger import logger  


def fetch_candles(symbol: str, resolution: str = "1h", limit: int = 200) -> pd.DataFrame | None:  
    """  
    Fetch candles from Delta API. resolution: '5m'|'1h'. limit candles.  
    """  
    interval_map = {'5m': 300, '1h': 3600}  # seconds  
    end = int(time.time())  
    start = end - (limit * interval_map.get(resolution, 3600))  


    url = f"{BASE_URL}/v2/history/candles"  
    params = {  
        "symbol": symbol,  
        "resolution": resolution,  
        "start": start,  
        "end": end  
    }  


    for attempt in range(3):  
        try:  
            logger.debug(f"Fetching {resolution} {symbol} (attempt {attempt+1}/3)")  
            response = requests.get(url, params=params, timeout=10)  
            response.raise_for_status()  
            data = response.json()  


            if "result" not in data or not data["result"]:  
                logger.warning(f"No {resolution} data for {symbol}")  
                return None  


            df = pd.DataFrame(  
                data["result"],  
                columns=["timestamp", "open", "high", "low", "close", "volume"]  
            )  


            for col in ["open", "high", "low", "close", "volume"]:  
                df[col] = pd.to_numeric(df[col], errors="coerce")  


            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")  
            df = df.sort_values("timestamp").reset_index(drop=True).dropna()  


            logger.debug(f"DEBUG: Fetched {len(df)} {resolution} candles {symbol}. ts: {df['timestamp'].iloc[-1]}, close: {df['close'].iloc[-1]:.4f}")  
            return df  


        except Exception as e:  
            logger.warning(f"{resolution} fetch {symbol} attempt {attempt+1}: {e}")  
            if attempt < 2:  
                time.sleep(2 ** attempt)  
    logger.error(f"{resolution} fetch failed {symbol}")  
    return None

