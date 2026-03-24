import typer
import pandas as pd
import numpy as np
from config import SYMBOLS
from indicators import indicators
from strategy import generate_5min_signal
from logger import logger
from fetch import fetch_candles as fetch

app = typer.Typer()

def simulate_trade(df: pd.DataFrame, entry_idx: int, signal: str, entry_price: float, 
                  risk_reward: float = 2.0) -> dict:
    """Proper trade simulation with TP/SL logic."""
    future_df = df.iloc[entry_idx:].copy()
    
    # Calculate TP/SL levels
    if signal == "BUY":
        sl_price = entry_price * 0.99  # 1% SL
        tp_price = entry_price * (1 + 0.025 * risk_reward)  # Align with live 2.5% TP
    else:  # SELL
        sl_price = entry_price * 1.01  # 1% SL
        tp_price = entry_price * (1 - 0.02 * risk_reward)  # 1:2 RR
    
    # Simulate trade exit
    for idx, row in future_df.iterrows():
        if signal == "BUY":
            if row['low'] <= sl_price:  # SL hit
                return {
                    "entry": entry_price,
                    "signal": signal,
                    "exit": sl_price,
                    "pnl": (sl_price - entry_price) / entry_price,
                    "exit_type": "SL"
                }
            if row['high'] >= tp_price:  # TP hit
                return {
                    "entry": entry_price,
                    "signal": signal,
                    "exit": tp_price,
                    "pnl": (tp_price - entry_price) / entry_price,
                    "exit_type": "TP"
                }
        else:  # SELL
            if row['high'] >= sl_price:  # SL hit
                return {
                    "entry": entry_price,
                    "signal": signal,
                    "exit": sl_price,
                    "pnl": (entry_price - sl_price) / entry_price,
                    "exit_type": "SL"
                }
            if row['low'] <= tp_price:  # TP hit
                return {
                    "entry": entry_price,
                    "signal": signal,
                    "exit": tp_price,
                    "pnl": (entry_price - tp_price) / entry_price,
                    "exit_type": "TP"
                }
    
    # If no exit found, close at last price
    last_price = future_df['close'].iloc[-1]
    pnl = (last_price - entry_price) / entry_price if signal == "BUY" else (entry_price - last_price) / entry_price
    return {
        "entry": entry_price,
        "signal": signal,
        "exit": last_price,
        "pnl": pnl,
        "exit_type": "END"
    }

@app.command()
def run(symbol: str = "BTCUSD", days: int = 30):
    """Run backtest for symbol over days."""
    logger.info(f"🚀 Backtesting {symbol} for {days} days")
    
    # Fetch more data for backtest (5min candles)
    df = fetch(symbol, limit=days * 288)  # ~288 5min candles per day
    if df is None or len(df) < 50:
        logger.error(f"❌ Failed to fetch sufficient data for {symbol}")
        raise typer.Exit(code=1)
    
    logger.info(f"📊 Loaded {len(df)} candles")
    
    # Apply indicators
    df = indicators(df)
    
    trades = []
    total_trades = 0
    
    # Walk-forward backtest (avoid look-ahead bias)
    for i in range(50, len(df) - 10):  # Leave buffer for simulation
        # Use only past data for signal
        signal_df = df.iloc[:i+1]
        signal = generate_5min_signal(signal_df)
        
        if signal in ["BUY", "SELL"]:
            total_trades += 1
            entry_price = df['close'].iloc[i]
            trade_result = simulate_trade(df, i, signal, entry_price)
            trades.append(trade_result)
            
            logger.debug(f"Trade #{len(trades)}: {signal} @ {entry_price:.4f} | PnL: {trade_result['pnl']:.3%}")
    
    if not trades:
        logger.warning("⚠️ No trades generated")
        typer.echo("No trading signals found.")
        raise typer.Exit(code=0)
    
    # Calculate metrics
    trades_df = pd.DataFrame(trades)
    win_rate = (trades_df['pnl'] > 0).mean()
    total_pnl = trades_df['pnl'].sum()
    avg_win = trades_df[trades_df['pnl'] > 0]['pnl'].mean()
    avg_loss = trades_df[trades_df['pnl'] < 0]['pnl'].mean()
    profit_factor = abs(avg_win * (win_rate * len(trades_df)) / (abs(avg_loss) * (1 - win_rate) * len(trades_df)))
    
    # Results table
    typer.echo("\n" + "="*60)
    typer.echo("📈 BACKTEST RESULTS")
    typer.echo("="*60)
    typer.echo(f"Symbol: {symbol} | Period: {days} days")
    typer.echo(f"Total Trades: {len(trades_df):,}")
    typer.echo(f"Win Rate: {win_rate:.1%}")
    typer.echo(f"Total PnL: {total_pnl:.2%}")
    typer.echo(f"Avg Win: {avg_win:.2%}" if not pd.isna(avg_win) else "Avg Win: N/A")
    typer.echo(f"Avg Loss: {avg_loss:.2%}" if not pd.isna(avg_loss) else "Avg Loss: N/A")
    typer.echo(f"Profit Factor: {profit_factor:.2f}")
    typer.echo(f"Best Trade: {trades_df['pnl'].max():.2%}")
    typer.echo(f"Worst Trade: {trades_df['pnl'].min():.2%}")
    typer.echo("="*60)
    
    # Save results
    trades_df.to_csv(f"backtest_{symbol}_{days}d.csv", index=False)
    logger.info(f"💾 Results saved to backtest_{symbol}_{days}d.csv")
    
    if win_rate > 0.5 and profit_factor > 1.2:
        typer.echo("✅ STRATEGY PROFITABLE!")
    else:
        typer.echo("⚠️ Strategy needs improvement")

@app.command()
def batch():
    """Run backtest for all symbols."""
    for symbol in SYMBOLS[:3]:  # Limit for testing
        typer.echo(f"\nRunning {symbol}...")
        run(symbol, days=7)

if __name__ == "__main__":
    app()