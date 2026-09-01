from feed import MarketDataFeed
from strategy import BollingerRSIStrategy
from engine import ExecutionEngine
from dashboard import TradingDashboard

if __name__ == "__main__":
    feed = MarketDataFeed(start_price=100.0, volatility=0.6)
    
    strategy = BollingerRSIStrategy(
        bb_period=20, 
        num_std_dev=2.0, 
        rsi_period=14, 
        trend_sma_period=50
    )
    
    engine = ExecutionEngine(
        initial_capital=10000.0, 
        stop_loss_amount=35.0, 
        max_hold_ticks=60,
        cooldown_ticks=30
    )

    app = TradingDashboard(
        feed=feed,
        strategy=strategy,
        engine=engine,
        units_per_trade=10.0,
        refresh_ms=2
    )
    app.run()