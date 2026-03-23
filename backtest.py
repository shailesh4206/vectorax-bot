import typer
import pandas as pd
from config import SYMBOLS
from indicators import indicators
from strategy import support_resistance
from logger import logger
from fetch import fetch  # Note: will update main.py later

app = typer.Typer()

@app.command()
def run(symbol: str = "BTCUSD", days: int = 30):
    """Run backtest for symbol over days."""
    logger.info(f"Backtesting {symbol} for {days} days")
    
    # Fetch more data for backtest
    df = fetch(symbol, limit=days * 288)  # ~5min * 288 per day
    if df is None:
        logger.error("Failed to fetch data")
        raise typer.Exit(code=1)
    
    df = indicators(df)
    trades = []
    
    for i in range(20, len(df)):
        signal = support_resistance(df.iloc[:i+1])
        if signal != "WAIT":
            entry = df['close'].iloc[i]
            sl = entry * 0.99 if signal == "BUY" else entry * 1.01
            tp = entry * (1 + 0.02 * 2) if signal == "BUY" else entry * (1 - 0.02 * 2)  # RR 1:2
            
            # Simulate exit (simple: next signals or TP/SL hit)
            future_df = df.iloc[i:]
            hit_tp = any((future_df['low'] <= sl) if signal == "BUY" else (future_df['high'] >= sl), future_df['high'] >= tp if signal == "BUY" else future_df['low'] <= tp)
            # Simplified P/L calculation
            
            trades.append({"entry": entry, "signal": signal, "pnl": 0.02})  # Placeholder
    
    logger.info(f"Backtest complete. {len(trades)} trades simulated.")
    typer.echo("Full metrics coming in next version.")

if __name__ == "__main__":
    app()

