# Vectorax Trading Bot for Delta Exchange

## Overview
Fully working Python crypto trading bot with **5-minute strategy + 1-hour confirmations**:
- **Strategy**: 5m S/R breakout + EMA50>200 trend + RSI filter (<70/>30) + volume spike (>1.2x avg). Confirmed by 1h trend/volume.
- **Risk-Reward**: 1:2.5 fixed
- **Risk Mgmt**: Balance >= $200 check, max 3 positions, 1% risk/trade.
- **Features**: UTF-8 logging, Telegram alerts, API retries, SL/TP auto-close, summary reports.
- **Deployment Ready**: Render Background Worker!

## Quick Start
1. Copy `.env.example` to `.env` and fill credentials.
2. `pip install -r requirements.txt`
3. `python main.py` (modular) or `python vectorax-trading-bot-single.py` (standalone).

## 🚀 Render Deployment (Fully Fixed)
1. `git add . && git commit -m "Fix Render: pinned deps, Procfile, env template" && git push`
2. Render → New > **Background Worker**
3. Connect GitHub repo/branch
4. Build: `pip install -r requirements.txt`
5. Start: `python main.py` (Procfile)
6. **Env Vars** (from .env.example):
   | Var | Example |
   |-----|---------|
   | DELTA_API_KEY | your_key |
   | DELTA_API_SECRET | your_secret |
   | TELEGRAM_TOKEN | bot_token |
   | TELEGRAM_CHAT_ID | chat_id |
   | TESTNET | true |
   | SYMBOLS | BTCUSD_PERP,ETHUSD_PERP |
7. Deploy → Success! Bot sends Telegram start alert.

**Fixes:** Pinned deps (no pip fail), no .env, worker Procfile, 3.11 runtime.

## Strategy Logic Summary
1. Fetch 5m candles (~300).
2. Compute indicators (EMA/RSI/vol/trend).
3. Signal on S/R break + 3 confirms.
4. 1h confirmation.
5. Execute with SL/TP.

## Files
- `main.py`: Core
- `Procfile`: Render
- `.env.example`: Template
- `requirements.txt`: Pinned

## Summary Report (summary.txt)
Generated each cycle: trades, capital, est return.

## Dependencies
`requirements.txt`. Python 3.11.9.

Testnet first! Logs: `logs/vectorax.log`, Telegram alerts.
