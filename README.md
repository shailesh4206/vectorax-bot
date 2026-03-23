# Vectorax Trading Bot for Delta Exchange

## Overview
Fully working Python crypto trading bot with **5-minute strategy + 1-hour confirmations**:
- **Strategy**: 5m S/R breakout + EMA50>200 trend + RSI filter (<70/>30) + volume spike (>1.2x avg). Confirmed by 1h trend/volume.
- **Risk-Reward**: 1:1.2 fixed
- **Risk Mgmt**: Balance >= $200 check, max 3 positions, 1.5% risk/trade dynamic sizing.
- **Features**: UTF-8 logging (console/rotating file), Telegram alerts, API retries, SL/TP auto-close, summary reports.
- **Deployment Ready**: `pip install -r requirements.txt && python main.py`

## Quick Start
1. Copy `.env.sample` to `.env` and fill credentials.
2. `pip install -r requirements.txt`
3. `python main.py` (modular) or `python vectorax-trading-bot-single.py` (standalone).

## Strategy Logic Summary
1. Fetch 5m candles (~300 recent).
2. Compute indicators (EMA/RSI/vol/trend).
3. Signal if price breaks 20-period S/R + all 3 confirmations.
4. Confirm with latest 1h candle trend/vol.
5. Execute if confirmed, market entry + logged SL/TP (auto-monitored).

## Files
- `main.py`: Core loop.
- `strategy.py`: 5m signal + 1h confirm.
- `*.py`: Modular (fetch, risk, etc.).
- `vectorax-trading-bot-single.py`: All-in-one deployable.

## Summary Report (summary.txt)
Generated each cycle/shutdown: trades count, capital delta, est monthly return (60% winrate assumed).

## Dependencies
See `requirements.txt`. Python 3.10+.

Testnet first! Monitor `logs/vectorax.log` + Telegram.

