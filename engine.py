from typing import Optional, List
from models import Trade

class ExecutionEngine:
    """Handles order execution, dynamic ATR stops, trailing profit locks, cooldowns, and equity tracking."""

    def __init__(
        self, 
        initial_capital: float = 10000.0, 
        atr_multiplier: float = 2.0, 
        max_hold_ticks: int = 60,
        cooldown_ticks: int = 30,
        use_trailing_stop: bool = True
    ):
        self.starting_capital = initial_capital
        self.atr_multiplier = atr_multiplier
        self.max_hold_ticks = max_hold_ticks
        self.cooldown_ticks = cooldown_ticks
        self.use_trailing_stop = use_trailing_stop
        
        self.position: str = "NONE"
        self.active_trade: Optional[Trade] = None
        self.trade_history: List[Trade] = []
        self.realized_pnl: float = 0.0
        self._trade_counter = 0
        self.last_stop_tick: int = -999

    def is_in_cooldown(self, current_tick: int) -> bool:
        """Blocks new entries for X ticks after a stop-loss trigger."""
        return (current_tick - self.last_stop_tick) < self.cooldown_ticks

    # engine.py update inside check_risk_exits
    def check_risk_exits(self, current_price: float, current_tick: int, current_atr: float) -> Optional[Trade]:
        if not self.active_trade or self.position != "LONG":
            return None

        trade = self.active_trade
        ticks_held = current_tick - trade.entry_tick
        unrealized = self.get_unrealized_pnl(current_price)

        # Pure ATR Stop-Loss (Initial Risk Level)
        if current_price <= trade.stop_price:
            self.last_stop_tick = current_tick
            return self._close_position(current_price, current_tick, reason="STOP_LOSS")

        # Time-Based Exit
        if ticks_held >= self.max_hold_ticks and unrealized <= 0.0:
            return self._close_position(current_price, current_tick, reason="TIME_EXIT")

        return None

    def place_order(self, order_type: str, price: float, units: float, tick: int, current_atr: float) -> Optional[Trade]:
        """Opens or closes positions with dynamic ATR stop placement."""
        order_type = order_type.upper()

        if order_type == "BUY" and self.position == "NONE":
            self._trade_counter += 1
            stop_dist = current_atr * self.atr_multiplier
            
            trade = Trade(
                trade_id=self._trade_counter,
                side="LONG",
                entry_price=price,
                entry_tick=tick,
                units=units,
                highest_price=price,
                stop_price=price - stop_dist
            )
            self.active_trade = trade
            self.position = "LONG"
            return trade

        if order_type == "SELL" and self.position == "LONG":
            return self._close_position(price, tick, reason="SIGNAL")

        return None

    def _close_position(self, exit_price: float, tick: int, reason: str = "SIGNAL") -> Optional[Trade]:
        if not self.active_trade:
            return None

        trade = self.active_trade
        trade.exit_price = exit_price
        trade.exit_tick = tick
        trade.is_open = False
        trade.exit_reason = reason
        trade.realized_pnl = (exit_price - trade.entry_price) * trade.units

        self.realized_pnl += trade.realized_pnl
        self.trade_history.append(trade)
        self.active_trade = None
        self.position = "NONE"

        return trade

    def get_unrealized_pnl(self, current_price: float) -> float:
        """Calculates unrealized PnL of an active position."""
        if not self.active_trade or self.position != "LONG":
            return 0.0
        return (current_price - self.active_trade.entry_price) * self.active_trade.units

    def get_equity(self, current_price: float) -> float:
        """Calculates total account equity (starting capital + realized PnL + unrealized PnL)."""
        return self.starting_capital + self.realized_pnl + self.get_unrealized_pnl(current_price)

    @property
    def win_rate(self) -> float:
        """Calculates historical trade win percentage."""
        if not self.trade_history:
            return 0.0
        wins = sum(1 for t in self.trade_history if t.realized_pnl > 0)
        return (wins / len(self.trade_history)) * 100.0