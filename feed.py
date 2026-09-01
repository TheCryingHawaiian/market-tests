import random
import pandas as pd
import yfinance as yf

class SimulatedMarketDataFeed:
    """Generates continuous synthetic tick price data."""
    def __init__(self, start_price: float = 100.0, volatility: float = 0.6):
        self.current_price = start_price
        self.volatility = volatility
        self.tick = 0

    def next_tick(self):
        self.tick += 1
        change = random.gauss(0, self.volatility)
        self.current_price = max(1.0, self.current_price + change)
        return self.tick, self.current_price


class HistoricalMarketDataFeed:
    """Streams real historical tick/candle data sequentially from Yahoo Finance or CSV."""
    
    def __init__(self, symbol: str = "AAPL", period: str = "730d", interval: str = "1h", csv_path: str = None):
        self.tick = 0
        
        if csv_path:
            df = pd.read_csv(csv_path)
            if 'Close' not in df.columns:
                raise ValueError("CSV file must contain a 'Close' price column.")
            self.prices = df['Close'].dropna().tolist()
        else:
            print(f"Fetching historical data for {symbol} ({period} at {interval} interval)...")
            df = yf.download(tickers=symbol, period=period, interval=interval, progress=False)
            
            if df.empty or 'Close' not in df:
                raise ValueError(f"Failed to retrieve price data for symbol '{symbol}'.")
                
            self.prices = df['Close'].values.flatten().tolist()
            print(f"Loaded {len(self.prices)} historical price candles.")

    def next_tick(self):
        if self.tick >= len(self.prices):
            # Holds the final price once historical data is exhausted
            return self.tick, float(self.prices[-1])
        
        price = float(self.prices[self.tick])
        self.tick += 1
        return self.tick, price


# Default alias for dashboard.py imports
MarketDataFeed = HistoricalMarketDataFeed