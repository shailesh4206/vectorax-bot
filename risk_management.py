from config import RISK_PERCENT, SL_PERCENT, TP_PERCENT, RR_RATIO, CAPITAL
from logger import logger
from execution import get_balance

def calculate_trade_params(side: str, entry: float, balance: float = None) -> dict:
    """
    Fixed % risk management for deployment:
    - Stoploss = 1% from entry
    - Target = 2% from entry  
    - Risk-Reward Ratio = 2.0
    - Position size = balance (risks exactly 1% of balance)
    - Min capital ₹200 check
    """
    # Get real balance
    balance = balance or get_balance()
    
    if balance < 200:
        logger.warning(f"Balance ${balance:.2f} < ₹200 min capital. Skipping trade.")
        return None
    
    risk_amount = balance * RISK_PERCENT  # 1% of balance
    
    # Fixed % distances
    sl_distance_pct = SL_PERCENT  # 0.01
    tp_distance_pct = TP_PERCENT  # 0.025
    
    sl_distance = entry * sl_distance_pct
    tp_distance = entry * tp_distance_pct
    
    # SL/TP prices
    if side == "BUY":
        sl_price = entry * (1 - sl_distance_pct)
        tp_price = entry * (1 + tp_distance_pct)
    else:  # SELL
        sl_price = entry * (1 + sl_distance_pct)
        tp_price = entry * (1 - tp_distance_pct)
    
    # Position size: risk_amount / sl_distance = balance * 0.01 / (entry * 0.01) = balance / entry
    size = risk_amount / sl_distance  # = balance / entry (full balance exposure at 1% risk)
    size = max(round(size, 3), 0.001)  # Min size, 3 decimals
    
    # Safety cap: don't exceed 95% balance value
    if size * entry > balance * 0.95:
        size = (balance * 0.95) / entry
        size = round(size, 3)
        logger.warning(f"Size capped to 95% balance: {size:.4f}")
    
    logger.info(f"📊 {side}: Entry ${entry:.4f} | SL ${sl_price:.4f} ({SL_PERCENT*100}%) | TP ${tp_price:.4f} ({TP_PERCENT*100}%) | Size {size:.4f} | Risk ${risk_amount:.2f}/{balance:.2f} (RR {RR_RATIO})")
    
    return {
        'size': size,
        'sl_price': sl_price,
        'tp_price': tp_price,
        'risk_amount': risk_amount
    }

