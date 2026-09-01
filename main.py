from feed import HistoricalMarketDataFeed
from strategy import FilteredTrendStrategy
from engine import CompoundingExecutionEngine
from dashboard import TradingDashboard

if __name__ == "__main__":
    feed = HistoricalMarketDataFeed(
        symbol="QQQ", 
        period="60d", 
        interval="15m"
    )
    
    strategy = FilteredTrendStrategy(
        breakout_period=20,
        exit_period=10,
        sma_period=50,
        rsi_period=14
    )
    
    engine = CompoundingExecutionEngine(
        initial_capital=10000.0, 
        atr_multiplier=2.5,
        equity_allocation_pct=0.95
    )

    app = TradingDashboard(
        feed=feed,
        strategy=strategy,
        engine=engine,
        refresh_ms=5
    )
    app.run()