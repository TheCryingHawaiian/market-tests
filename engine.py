from typing import List, Optional
from models import Trade

class ExecutionEngine:
    """Handles positions, automated risk exits, and post-stop cooldowns."""
    
    def __init__(self, initial_capital: float = 10000.0, 
                 stop_loss_amount: float = 35.0, 
                 max_hold_ticks: int = 60,
                 cooldown_ticks: int = 30):
        self.starting_capital = initial_capital
        self.stop_loss_amount = stop_loss_amount
        self.max_hold_ticks = max_hold_ticks
        self.cooldown_ticks = cooldown_ticks
        
        self.position: str = "NONE"
        self.active_trade: Optional[Trade] = None
        self.trade_history: List[Trade] = []
        self.realized_pnl: float = 0.0
        self._trade_counter = 0
        self.last_stop_tick: int = -999

    def is_in_cooldown(self, current_tick: int) -> bool:
        """Blocks new entries for N ticks after a stop-loss exit."""
        return (current_tick - self.last_stop_tick) < self.cooldown_ticks

    def check_risk_exits(self, current_price: float, current_tick: int) -> Optional[Trade]:
        """Evaluates active position for Stop Loss or Time Exit."""
        if not self.active_trade or self.position != "LONG":
            return None

        unrealized = self.get_unrealized_pnl(current_price)
        ticks_held = current_tick - self.active_trade.entry_tick

        if unrealized <= -self.stop_loss_amount:
            self.last_stop_tick = current_tick
            return self._close_position(current_price, current_tick, reason="STOP_LOSS")

        if ticks_held >= self.max_hold_ticks and unrealized <= 0.0:
            return self._close_position(current_price, current_tick, reason="TIME_EXIT")

        return None

    def place_order(self, order_type: str, price: float, units: float, tick: int) -> Optional[Trade]:
        order_type = order_type.upper()
        if order_type not in ("BUY", "SELL"):
            return None

        if order_type == "BUY":
            if self.position == "NONE":
                self._trade_counter += 1
                trade = Trade(
                    trade_id=self._trade_counter,
                    side="LONG",
                    entry_price=price,
                    entry_tick=tick,
                    units=units
                )
                self.active_trade = trade
                self.position = "LONG"
                return trade
            return None

        if order_type == "SELL":
            if self.position == "LONG":
                return self._close_position(price, tick, reason="SIGNAL")
            return None

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