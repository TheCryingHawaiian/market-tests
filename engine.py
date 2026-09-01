from typing import Optional, List
from models import Trade

class CompoundingExecutionEngine:
    """Execution engine with dynamic equity compounding and ATR trailing stops."""

    def __init__(self, initial_capital: float = 10000.0, atr_multiplier: float = 2.5, equity_allocation_pct: float = 0.95):
        self.starting_capital = initial_capital
        self.atr_multiplier = atr_multiplier
        self.allocation_pct = equity_allocation_pct
        
        self.position: str = "NONE"
        self.active_trade: Optional[Trade] = None
        self.trade_history: List[Trade] = []
        self.realized_pnl: float = 0.0
        self._trade_counter = 0

    def calculate_units(self, current_price: float) -> float:
        """Calculates dynamic share size using 95% of current total equity."""
        current_equity = self.starting_capital + self.realized_pnl
        allocated_cash = current_equity * self.allocation_pct
        return max(round(allocated_cash / current_price, 4), 1.0)

    def check_risk_exits(self, current_price: float, current_tick: int, current_atr: float) -> Optional[Trade]:
        if not self.active_trade or self.position != "LONG":
            return None

        trade = self.active_trade
        stop_distance = current_atr * self.atr_multiplier

        # Trail the stop upward behind high watermarks
        if current_price > trade.highest_price:
            trade.highest_price = current_price
            new_stop = trade.highest_price - stop_distance
            if new_stop > trade.stop_price:
                trade.stop_price = new_stop

        # Chandelier Trailing Stop Exit
        if current_price <= trade.stop_price:
            return self._close_position(current_price, current_tick, reason="TRAILING_STOP")

        return None

    def place_order(self, order_type: str, price: float, tick: int, current_atr: float) -> Optional[Trade]:
        order_type = order_type.upper()

        if order_type == "BUY" and self.position == "NONE":
            self._trade_counter += 1
            units = self.calculate_units(price)
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
        if not self.active_trade or self.position != "LONG":
            return 0.0
        return (current_price - self.active_trade.entry_price) * self.active_trade.units

    def get_equity(self, current_price: float) -> float:
        return self.starting_capital + self.realized_pnl + self.get_unrealized_pnl(current_price)

    @property
    def win_rate(self) -> float:
        if not self.trade_history:
            return 0.0
        wins = sum(1 for t in self.trade_history if t.realized_pnl > 0)
        return (wins / len(self.trade_history)) * 100.0