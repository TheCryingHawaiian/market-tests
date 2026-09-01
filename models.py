from dataclasses import dataclass
from typing import Optional

@dataclass
class Trade:
    trade_id: int
    side: str          # "LONG" or "SHORT"
    entry_price: float
    entry_tick: int
    units: float
    exit_price: Optional[float] = None
    exit_tick: Optional[int] = None
    realized_pnl: float = 0.0
    is_open: bool = True
    exit_reason: str = "OPEN"  # "OPEN", "SIGNAL", "STOP_LOSS", "TIME_EXIT"