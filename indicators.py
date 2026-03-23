def indicators(df):
    """
    Enhanced indicators with basic filters.
    """
    # EMAs
    df['EMA50'] = df['close'].ewm(span=50).mean()
    df['EMA200'] = df['close'].ewm(span=200).mean()
    
    # RSI
    delta = df['close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Volume
    df['VOL_AVG'] = df['volume'].rolling(5).mean()
    df['VOL_CONFIRM'] = df['volume'] > df['VOL_AVG'] * 1.2  # Volume spike
    
    # Trend filter
    df['TREND_UP'] = df['EMA50'] > df['EMA200']
    
    return df

