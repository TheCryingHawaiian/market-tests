from typing import List
import matplotlib.pyplot as plt
import matplotlib.animation as animation

from feed import HistoricalMarketDataFeed
from strategy import BollingerRSIStrategy
from engine import ExecutionEngine
from exporter import export_session_data

class TradingDashboard:
    """Renders execution visualization and handles step evaluation."""
    
    def __init__(self, feed: HistoricalMarketDataFeed, strategy: BollingerRSIStrategy, 
                 engine: ExecutionEngine, units_per_trade: float = 10.0, 
                 max_window: int = 100, refresh_ms: int = 10):
        
        self.feed = feed
        self.strategy = strategy
        self.engine = engine
        self.units = units_per_trade
        self.max_window = max_window
        self.refresh_ms = refresh_ms

        self.prices: List[float] = []
        self.ticks: List[int] = []
        self.equity_curve: List[float] = []
        
        self.buy_ticks, self.buy_prices = [], []
        self.sell_ticks, self.sell_prices = [], []

        self.fig, (self.ax_price, self.ax_pnl) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
        self.fig.canvas.mpl_connect('close_event', self._on_close)
        self.setup_chart()

    def setup_chart(self):
        self.line_price, = self.ax_price.plot([], [], color="royalblue", lw=1.5, label="Price")
        self.dots_buy, = self.ax_price.plot([], [], "go", markersize=7, label="BUY Execution", zorder=5)
        self.dots_sell, = self.ax_price.plot([], [], "ro", markersize=7, label="SELL Execution", zorder=5)
        self.ax_price.set_ylabel("Price")
        self.ax_price.set_title("Live Execution Dashboard")
        self.ax_price.legend(loc="upper right")
        
        self.line_equity, = self.ax_pnl.plot([], [], color="darkgreen", lw=1.5, label="Account Equity")
        self.ax_pnl.axhline(self.engine.starting_capital, color="gray", linestyle="--", alpha=0.6)
        self.ax_pnl.set_ylabel("Equity ($)")
        self.ax_pnl.set_xlabel("Tick")
        self.ax_pnl.legend(loc="upper right")

        self.label = self.ax_price.text(0.01, 0.95, "", transform=self.ax_price.transAxes,
                                        fontsize=10, fontfamily="monospace", va="top")

    def animate(self, frame):
        tick, price = self.feed.next_tick()
        self.ticks.append(tick)
        self.prices.append(price)

        # 1. Calculate current market ATR
        current_atr = self.strategy.calculate_atr(self.prices)

        # 2. Check risk exits (ATR Stop Loss / Trailing Stop / Time Exit)
        risk_trade = self.engine.check_risk_exits(price, tick, current_atr)
        if risk_trade:
            self.sell_ticks.append(tick)
            self.sell_prices.append(price)

        # 3. Check strategy signals if not in post-stop cooldown
        if not self.engine.is_in_cooldown(tick):
            signal = self.strategy.generate_signal(self.prices)
            if signal in ("BUY", "SELL"):
                executed_trade = self.engine.place_order(signal, price, self.units, tick, current_atr)
                if executed_trade:
                    if signal == "BUY":
                        self.buy_ticks.append(tick)
                        self.buy_prices.append(price)
                    elif signal == "SELL":
                        self.sell_ticks.append(tick)
                        self.sell_prices.append(price)

        current_equity = self.engine.get_equity(price)
        self.equity_curve.append(current_equity)

        vis_ticks = self.ticks[-self.max_window:]
        vis_prices = self.prices[-self.max_window:]
        vis_equity = self.equity_curve[-self.max_window:]
        min_tick, max_tick = vis_ticks[0], vis_ticks[-1] + 1

        self.line_price.set_data(vis_ticks, vis_prices)
        v_buys = [(t, p) for t, p in zip(self.buy_ticks, self.buy_prices) if min_tick <= t <= max_tick]
        v_sells = [(t, p) for t, p in zip(self.sell_ticks, self.sell_prices) if min_tick <= t <= max_tick]
        
        self.dots_buy.set_data([t[0] for t in v_buys], [t[1] for t in v_buys])
        self.dots_sell.set_data([t[0] for t in v_sells], [t[1] for t in v_sells])

        pad_price = max((max(vis_prices) - min(vis_prices)) * 0.1, 0.5)
        self.ax_price.set_ylim(min(vis_prices) - pad_price, max(vis_prices) + pad_price)
        self.ax_price.set_xlim(min_tick, max_tick)

        self.line_equity.set_data(vis_ticks, vis_equity)
        pad_eq = max((max(vis_equity) - min(vis_equity)) * 0.1, 5.0)
        self.ax_pnl.set_ylim(min(vis_equity) - pad_eq, max(vis_equity) + pad_eq)

        unrealized = self.engine.get_unrealized_pnl(price)
        cooldown_str = " (COOLDOWN)" if self.engine.is_in_cooldown(tick) else ""
        self.label.set_text(
            f"Price:      {price:.2f}\n"
            f"ATR:        {current_atr:.2f}\n"
            f"Position:   {self.engine.position}{cooldown_str}\n"
            f"Realized:   ${self.engine.realized_pnl:+.2f}\n"
            f"Unrealized: ${unrealized:+.2f}\n"
            f"Equity:     ${current_equity:.2f}\n"
            f"Win Rate:   {self.engine.win_rate:.1f}% ({len(self.engine.trade_history)} Trades)"
        )

    def _on_close(self, event):
        last_price = self.prices[-1] if self.prices else 0.0
        export_session_data(self.engine, current_price=last_price)

    def run(self):
        self.ani = animation.FuncAnimation(
            self.fig, self.animate, interval=self.refresh_ms, cache_frame_data=False
        )
        plt.tight_layout()
        plt.show()