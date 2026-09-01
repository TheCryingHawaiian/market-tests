from feed import HistoricalMarketDataFeed  # Or BulkCSVDataFeed
from strategy import BollingerRSIStrategy
from engine import ExecutionEngine
from dashboard import TradingDashboard

if __name__ == "__main__":
    # Load historical 5m AAPL candles or local CSV file
    feed = HistoricalMarketDataFeed(
        symbol="AAPL", 
        period="60d", 
        interval="5m"
    )
    
    strategy = BollingerRSIStrategy(
        bb_period=20, 
        num_std_dev=2.0, 
        rsi_period=14, 
        rsi_oversold=30.0,
        rsi_overbought=70.0,
        trend_sma_period=50
    )
    
    # main.py updates
    engine = ExecutionEngine(
        initial_capital=10000.0, 
        atr_multiplier=3.5,        # Wider stop buffer prevents noise stop-outs
        max_hold_ticks=60,         
        cooldown_ticks=30,         
        use_trailing_stop=False    # Disabled trailing stop for mean reversion
    )

    app = TradingDashboard(
        feed=feed,
        strategy=strategy,
        engine=engine,
        units_per_trade=10.0,
        refresh_ms=10
    )
    app.run()