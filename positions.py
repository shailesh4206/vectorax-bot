import json
import os
from typing import Dict, Optional, List
from dataclasses import dataclass
from config import MAX_TRADES

@dataclass
class Position:
    symbol: str
    side: str
    size: float
    entry: float
    sl: float
    tp: float
    timestamp: float

import time

class PositionsTracker:
    def __init__(self, file_path: str = 'positions.json'):
        self.file_path = file_path
        self.positions: Dict[str, Position] = {}
        self.load()

    def load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    data = json.load(f)
                    self.positions = {k: Position(**v) for k, v in data.items()}
            except Exception as e:
                print(f"Load positions error: {e}")

    def save(self):
        try:
            with open(self.file_path, 'w') as f:
                json.dump({sym: pos.__dict__ for sym, pos in self.positions.items()}, f, indent=2)
        except Exception as e:
            print(f"Save positions error: {e}")

    def add_position(self, symbol: str, side: str, size: float, entry: float, sl: float, tp: float, timestamp: float = time.time()):
        if len(self.positions) >= MAX_TRADES:
            return False
        if symbol in self.positions:
            return False  # Already open
        self.positions[symbol] = Position(symbol, side, size, entry, sl, tp, timestamp)
        self.save()
        return True

    def close_position(self, symbol: str):
        if symbol in self.positions:
            del self.positions[symbol]
            self.save()
            return True
        return False

    def get_open(self) -> List[Position]:
        return list(self.positions.values())

    def has_position(self, symbol: str) -> bool:
        return symbol in self.positions

    def get_position(self, symbol: str) -> Optional[Position]:
        return self.positions.get(symbol)

# Global instance
tracker = PositionsTracker()

