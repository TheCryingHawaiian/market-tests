from dataclasses import dataclass
from typing import Optional

@dataclass
class Trade:
    trade_id: int
    side: str
    entry_price: float
    entry_tick: int
    units: float
    exit_price: Optional[float] = None
    exit_tick: Optional[int] = None
    realized_pnl: float = 0.0
    is_open: bool = True
    exit_reason: str = "OPEN"
    highest_price: float = 0.0  # Dynamic peak price for trailing stop tracking
    stop_price: float = 0.0     # Dynamic volatility stop level