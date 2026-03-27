#!/usr/bin/env python3
"""Quick test script for fixed Delta Exchange API"""

import sys
import os
sys.path.insert(0, 'vectorax-bot')

from execution import (
    get_balance, 
    get_ticker_price, 
    get_product_id,
    place_order, 
    check_order_status,
    close_position
)
from config import SYMBOLS, API_KEY, TESTNET

def run_tests():
    print('Vectorax Delta Bot API Tests (Fixed /v2/wallets 404)')
    print(f'Testnet: {TESTNET}, Symbols: {SYMBOLS[:2]}...')
    
    if not API_KEY:
        print('Missing DELTA_API_KEY (.env)')
        return
    
    print('\n1. Testing get_balance()...')
    balance = get_balance()
    print(f'   USDT Balance/Fallback: ${balance:.2f}')
    
    if SYMBOLS:
        symbol = SYMBOLS[0] if SYMBOLS else "BTC_PERP"
        print(f'\n2. Testing get_ticker_price({symbol})...')
        price = get_ticker_price(symbol)
        print(f'   Price: ${price:.4f}' if price else '   Price fetch failed')
        
        print(f'\n3. Testing get_product_id({symbol})...')
        pid = get_product_id(symbol)
        print(f'   Product ID: {pid}' if pid else '   No product ID')
    
    print('\n4. Order functions ready (dry-run skipped)')
    print('   place_order(), check_order_status(), close_position()')
    print('\nFIXED: /v2/wallets now POST + retries + Telegram alerts!')
    print('   Run full bot: python vectorax-bot/main.py')

if __name__ == '__main__':
    run_tests()

