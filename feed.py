import yfinance as yf
import pandas as pd

class HistoricalMarketDataFeed:
    """Historical market data feed stream powered by Yahoo Finance.
    
    Includes automatic unit conversion from pence (GBX) to pounds (£) for London Stock Exchange (.L) tickers.
    """
    
    def __init__(self, symbol: str = "ISF.L", period: str = "60d", interval: str = "5m"):
        self.symbol = symbol
        self.period = period
        self.interval = interval
        self._current_idx = 0
        
        # Fetch price history from Yahoo Finance
        ticker = yf.Ticker(self.symbol)
        self.df = ticker.history(period=self.period, interval=self.interval)
        
        if self.df.empty:
            raise ValueError(f"No data returned for ticker '{self.symbol}'. Verify internet connection or ticker validity.")
        
        # Clean price series
        raw_prices = self.df["Close"].dropna().tolist()
        
        # Automatically convert London GBX (pence) prices to GBP (£)
        if self.symbol.upper().endswith(".L"):
            self.prices = [p / 100.0 for p in raw_prices]
        else:
            self.prices = raw_prices

    def next_tick(self) -> tuple[int, float]:
        """Returns the next (tick_index, price) tuple from the historical stream."""
        if self._current_idx >= len(self.prices):
            # Maintain final price state if the stream reaches the end of historical data
            return self._current_idx, self.prices[-1]
        
        tick = self._current_idx
        price = self.prices[tick]
        self._current_idx += 1
        
        return tick, price

    def reset(self):
        """Resets the feed stream back to tick 0."""
        self._current_idx = 0