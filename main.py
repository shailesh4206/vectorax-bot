import time
import pandas as pd
import requests
import signal
import sys
import os
from config import SYMBOLS, LOG_LEVEL, MAX_TRADES, SUMMARY_FILE_PATH, BASE_URL
from logger import logger, setup_logger
from telegram_alerts import send_alert
from fetch import fetch_candles
from indicators import indicators
from strategy import generate_5min_signal, confirm_with_1h
from risk_management import calculate_trade_params
from execution import place_order, get_balance, get_ticker_price, close_position
from positions import tracker

# Setup logger
setup_logger()

# Health check
def health_check():
    try:
        resp = requests.get(f"{BASE_URL}/v2/products?limit=1", timeout=10)
        if resp.status_code == 200:
            logger.info("✅ API health check passed")
            return True
        logger.error(f"API health check failed: {resp.status_code}")
        return False
    except Exception as e:
        logger.error(f"API health check exception: {e}")
        return False

if not health_check():
    sys.exit(1)

# Graceful shutdown
def signal_handler(sig, frame):
    logger.info("Shutdown signal received. Closing bot safely...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Summary report
trade_stats = {
    'cycles': 0,
    'trades_executed': 0,
    'capital_start': 0.0,
    'capital_end': 0.0
}

def write_summary():
    capital_used = trade_stats['capital_start'] - trade_stats['capital_end']
    est_monthly_trades = 20
    win_rate = 0.6
    avg_win = 0.025
    avg_loss = -0.01
    expected_return_per_trade = (win_rate * avg_win) + ((1-win_rate) * avg_loss)
    est_monthly_pct = est_monthly_trades * expected_return_per_trade * 100
    
    summary = f"""Vectorax Trading Bot Summary
Strategy: 5-minute S/R breakout + EMA/RSI/volume/trend confirmations + 1h HTF validation
Risk Management: Stoploss=1%, Target=2.5%, RR=2.5, Max 3 positions, Min capital ₹200
Number of cycles: {trade_stats['cycles']}
Number of trades executed: {trade_stats['trades_executed']}
Capital start: ₹{trade_stats['capital_start']:.2f} | Remaining: ₹{trade_stats['capital_end']:.2f} | Used: ₹{capital_used:.2f}
Example monthly return (20 trades, 60% win rate): ~{est_monthly_pct:.1f}%
"""
    with open(SUMMARY_FILE_PATH, 'a', encoding='utf-8') as f:
        f.write("\n" + summary + "="*80 + "\n")
    logger.info(f"📋 Summary written to {SUMMARY_FILE_PATH}")

# SL/TP Monitor & Close
def monitor_positions():
    """Check SL/TP for open positions each cycle."""
    for pos in tracker.get_open():
        current_price = get_ticker_price(pos.symbol)
        if current_price is None:
            continue

        closed = False
        reason = ""
        if pos.side == "BUY":
            if current_price <= pos.sl:
                close_position(pos.symbol, pos.side, pos.size)
                reason = "STOP LOSS (1%)"
                closed = True
            elif current_price >= pos.tp:
                close_position(pos.symbol, pos.side, pos.size)
                reason = "TAKE PROFIT (2%)"
                closed = True
        else:  # SELL
            if current_price >= pos.sl:
                close_position(pos.symbol, pos.side, pos.size)
                reason = "STOP LOSS (1%)"
                closed = True
            elif current_price <= pos.tp:
                close_position(pos.symbol, pos.side, pos.size)
                reason = "TAKE PROFIT (2%)"
                closed = True

        if closed:
            alert = f"🔒 {pos.symbol} {pos.side} CLOSED: {reason}\nPrice: {current_price:.4f}\nEntry: {pos.entry:.4f}"
            send_alert(alert)
            logger.info(f"{alert}")

# Startup
logger.info("🚀 Vectorax Trading Bot Started - 5m S/R + Multi-confirm + 1h HTF + 1%/2% RR2.0 🚀")
send_alert("🚀 Vectorax Trading Bot Deployed - SL1% TP2% Max3pos Min₹200!")

balance = get_balance()
trade_stats['capital_start'] = balance
logger.info(f"Initial balance: ₹{balance:.2f}")

# Main Loop
while True:
    try:
        trade_stats['cycles'] += 1
        open_positions = len(tracker.get_open())
        balance = get_balance()
        trade_stats['capital_end'] = balance
        logger.info(f"Cycle #{trade_stats['cycles']} | Positions: {open_positions}/{MAX_TRADES} | Balance: ₹{balance:.2f}")

        if balance < 200:
            logger.warning(f"LOW BALANCE ₹{balance:.2f} < ₹200. Skipping trades.")
            send_alert(f"⚠️ LOW BALANCE ₹{balance:.2f} < ₹200 - Skipping")
            write_summary()
            time.sleep(60)
            continue

        # Monitor existing positions
        monitor_positions()

        open_positions = len(tracker.get_open())
        if open_positions >= MAX_TRADES:
            logger.info("Max 3 positions reached. Waiting 1h")
            pos_summary = "\n".join([f"{p.symbol} {p.side} SL:{p.sl:.4f} TP:{p.tp:.4f}" for p in tracker.get_open()])
            send_alert(f"📊 Max positions ({open_positions}):\n{pos_summary}")
            write_summary()
        else:
            for symbol in SYMBOLS:
                if tracker.has_position(symbol):
                    logger.debug(f"Skip {symbol} (position open)")
                    continue

                logger.info(f"Scanning {symbol} for 5m breakout + 1h confirm...")

                df_5m = fetch_candles(symbol, '5m', 300)
                df_1h = fetch_candles(symbol, '1h', 50)

                if df_5m is None or len(df_5m) < 50 or df_1h is None or len(df_1h) < 20:
                    logger.warning(f"Insufficient data {symbol} 5m:{len(df_5m) or 0} 1h:{len(df_1h) or 0}")
                    continue

                signal_5m = generate_5min_signal(df_5m)
                if signal_5m == "WAIT":
                    continue

                if not confirm_with_1h(df_1h, signal_5m):
                    continue

                logger.info(f"🚀 {signal_5m} SIGNAL CONFIRMED w/ multi-confirmations {symbol}")

                entry_price = df_5m["close"].iloc[-1]
                params = calculate_trade_params(signal_5m, entry_price)
                if params is None:
                    logger.warning(f"Risk params invalid for {symbol}")
                    continue

                result = place_order(symbol, signal_5m, params["size"], params["tp_price"], params["sl_price"])
                if result["success"]:
                    tracker.add_position(symbol, signal_5m, params["size"], entry_price, params["sl_price"], params["tp_price"])
                    trade_stats['trades_executed'] += 1
                    alert = f"✅ {symbol} {signal_5m}\nEntry: ₹{entry_price:.4f}\nSize: {params['size']}\nSL: ₹{params['sl_price']:.4f} (1%)\nTP: ₹{params['tp_price']:.4f} (2%)"
                    send_alert(alert)
                    logger.info(f"✅ Trade #{trade_stats['trades_executed']} executed {symbol}")
                else:
                    logger.error(f"❌ Order failed {symbol}: {result.get('error', 'Unknown')}")

        logger.info("Cycle complete. Sleeping 1h ⏰")
        write_summary()
        time.sleep(3600)

    except KeyboardInterrupt:
        logger.info("🛑 Manual stop")
        break
    except Exception as e:
        logger.error(f"Cycle exception: {e}", exc_info=True)
        time.sleep(60)

# Final report
write_summary()
final_open = len(tracker.get_open())
logger.info(f"🏁 Bot stopped. Cycles: {trade_stats['cycles']} | Trades: {trade_stats['trades_executed']} | Open: {final_open}")
send_alert(f"🏁 Bot STOPPED | Trades: {trade_stats['trades_executed']} | Open: {final_open} | See summary.txt & logs/vectorax.log")