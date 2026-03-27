from logger import logger
from indicators import indicators


def generate_5min_signal(df_5m: pd.DataFrame) -> str:
    """
    Generate signal from 5-minute candles (S/R breakout + multiple confirmations).
    """
    if len(df_5m) < 50:  # Need more data for EMAs
        logger.debug("Insufficient 5m data")
        return "WAIT"
    
    df_5m = indicators(df_5m)
    
    # S/R levels on 5m
    support = df_5m['close'].rolling(20).min().iloc[-1]
    resistance = df_5m['close'].rolling(20).max().iloc[-1]
    
    price = df_5m['close'].iloc[-1]
    rsi = df_5m['RSI'].iloc[-1]
    vol_confirm = df_5m['VOL_CONFIRM'].iloc[-1]
    trend_up = df_5m['TREND_UP'].iloc[-1]
    
    # BUY: breakout + all confirmations
    if (price > resistance * 1.001 and 
        trend_up and 
        vol_confirm and 
        rsi < 70):
        logger.info(f"🎯 5m BUY signal: price {price:.4f} > R {resistance:.4f} | trend {trend_up} vol {vol_confirm} RSI {rsi:.1f}")
        return "BUY"
    
    # SELL: breakdown + confirmations
    trend_down = not trend_up
    if (price < support * 0.999 and
        trend_down and 
        vol_confirm and 
        rsi > 30):
        logger.info(f"🎯 5m SELL signal: price {price:.4f} < S {support:.4f} | trend {trend_down} vol {vol_confirm} RSI {rsi:.1f}")
        return "SELL"
    
    return "WAIT"


def confirm_with_1h(df_1h: pd.DataFrame, signal: str) -> bool:
    """
    Confirm 5m signal with 1-hour candle (higher timeframe accuracy).
    """
    if len(df_1h) < 20 or signal == "WAIT":
        return False
    
    df_1h = indicators(df_1h)
    trend_up_1h = df_1h['TREND_UP'].iloc[-1]
    vol_confirm_1h = df_1h['VOL_CONFIRM'].iloc[-1]
    
    if signal == "BUY" and trend_up_1h and vol_confirm_1h:
        logger.info("✅ 1h CONFIRMS 5m BUY")
        return True
    if signal == "SELL" and not trend_up_1h and vol_confirm_1h:
        logger.info("✅ 1h CONFIRMS 5m SELL")
        return True
    
    logger.info(f"❌ 1h REJECTS {signal} (trend:{'UP' if trend_up_1h else 'DOWN'} vol:{vol_confirm_1h})")
    return False

