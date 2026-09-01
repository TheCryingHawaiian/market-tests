import random

class MarketDataFeed:
    """Generates continuous simulated tick price data."""
    
    def __init__(self, start_price: float = 100.0, volatility: float = 0.6):
        self.current_price = start_price
        self.volatility = volatility
        self.tick = 0

    def next_tick(self):
        self.tick += 1
        change = random.gauss(0, self.volatility)
        self.current_price = max(1.0, self.current_price + change)
        return self.tick, self.current_price