import random
import numpy as np
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
    """Streams historical tick/candle data directly from Yahoo Finance."""

    def __init__(self, symbol: str = "AAPL", period: str = "5d", interval: str = "1m", csv_path: str = None):
        self.tick = 0
        
        if csv_path:
            df = pd.read_csv(csv_path)
            clean_series = pd.to_numeric(pd.Series(df['Close'].values.flatten()), errors='coerce').dropna()
            self.prices = clean_series.tolist()
        else:
            print(f"Fetching historical data for {symbol} ({period} at {interval} interval)...")
            df = yf.download(tickers=symbol, period=period, interval=interval, progress=False)
            
            if df.empty or 'Close' not in df:
                raise ValueError(f"Failed to retrieve price data for symbol '{symbol}'.")
                
            # Wrap in pd.Series so .dropna() works cleanly after pd.to_numeric
            clean_series = pd.to_numeric(pd.Series(df['Close'].values.flatten()), errors='coerce').dropna()
            self.prices = clean_series.tolist()
            print(f"Loaded {len(self.prices):,} historical price candles.")

    def next_tick(self):
        if self.tick >= len(self.prices):
            return self.tick, float(self.prices[-1])
        
        price = float(self.prices[self.tick])
        self.tick += 1
        return self.tick, price


class BulkCSVDataFeed:
    """Streams historical datasets from local CSV files, safely stripping string artifacts."""

    def __init__(self, csv_path: str, price_col: str = "Close"):
        self.tick = 0
        print(f"Loading bulk market data from {csv_path}...")
        
        df = pd.read_csv(csv_path, low_memory=False)
        
        # Match price column flexibly across cases
        cols_lower = {str(col).lower(): col for col in df.columns}
        if price_col.lower() in cols_lower:
            target_col = cols_lower[price_col.lower()]
        else:
            matching_cols = [c for c in df.columns if price_col.lower() in str(c).lower()]
            if matching_cols:
                target_col = matching_cols[0]
            else:
                raise KeyError(f"Could not find column '{price_col}'. Available columns: {list(df.columns)}")

        # Convert non-numeric values (like ticker headers 'AAPL') to NaN and purge
        clean_series = pd.to_numeric(df[target_col], errors='coerce').dropna()
        self.prices = clean_series.tolist()
        
        if not self.prices:
            raise ValueError(f"No valid numeric price data found in column '{target_col}'.")
            
        print(f"Successfully loaded {len(self.prices):,} valid price candles.")

    def next_tick(self):
        if self.tick >= len(self.prices):
            return self.tick, float(self.prices[-1])
        
        price = float(self.prices[self.tick])
        self.tick += 1
        return self.tick, price


class HighVolumeSyntheticFeed:
    """Generates large synthetic price paths using Geometric Brownian Motion."""

    def __init__(self, start_price: float = 100.0, num_ticks: int = 100000, mu: float = 0.00005, sigma: float = 0.002):
        self.tick = 0
        returns = np.random.normal(loc=mu, scale=sigma, size=num_ticks)
        price_paths = start_price * np.exp(np.cumsum(returns))
        self.prices = price_paths.tolist()
        print(f"Generated {len(self.prices):,} synthetic ticks.")

    def next_tick(self):
        if self.tick >= len(self.prices):
            return self.tick, float(self.prices[-1])
        
        price = float(self.prices[self.tick])
        self.tick += 1
        return self.tick, price


# Default alias for backward compatibility
MarketDataFeed = HistoricalMarketDataFeed