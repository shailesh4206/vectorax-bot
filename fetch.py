import time
import pandas as pd
import requests
from config import BASE_URL
from logger import logger

def fetch_candles(symbol: str, resolution: str = "1h", limit: int = 200) -> pd.DataFrame:
    """
    Fetch candles from Delta API.
    resolution: '5m' | '1h'
    limit: number of candles
    Returns a pandas DataFrame with columns: timestamp, open, high, low, close, volume
    """
    interval_map = {'5m': 300, '1h': 3600}  # seconds per candle
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
            logger.debug(f"Fetching {resolution} candles for {symbol}, attempt {attempt+1}/3")
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Safety check
            if not data.get("result"):
                logger.warning(f"No candle data for {symbol} ({resolution})")
                return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

            df = pd.DataFrame(data["result"])

            # Ensure all necessary columns exist
            for col in ["timestamp", "open", "high", "low", "close", "volume"]:
                if col not in df.columns:
                    df[col] = 0

            # Convert numeric columns safely
            numeric_cols = ["open", "high", "low", "close", "volume"]
            df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce").fillna(0)

            # Convert timestamp to datetime
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s", errors="coerce")
            df = df.dropna(subset=["timestamp"])

            # Sort by timestamp
            df = df.sort_values("timestamp").reset_index(drop=True)

            logger.debug(f"Fetched {len(df)} candles for {symbol} ({resolution}). Last close: {df['close'].iloc[-1]:.4f}")
            return df

        except requests.exceptions.RequestException as e:
            logger.warning(f"{resolution} fetch {symbol} attempt {attempt+1} failed: {e}")
            if attempt < 2:
                time.sleep(2 ** attempt)
        except Exception as e:
            logger.error(f"Unexpected error fetching {symbol} {resolution}: {e}")
            break

    logger.error(f"Failed to fetch {resolution} candles for {symbol} after 3 attempts")
    return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])