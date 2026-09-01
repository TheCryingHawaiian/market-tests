import numpy as np

class FilteredTrendStrategy:
    """Trend-following strategy with calibrated RSI momentum and parabolic stretch filters."""

    def __init__(self, breakout_period: int = 20, exit_period: int = 10, sma_period: int = 50, rsi_period: int = 14, atr_period: int = 14):
        self.breakout_period = breakout_period
        self.exit_period = exit_period
        self.sma_period = sma_period
        self.rsi_period = rsi_period
        self.atr_period = atr_period

    def calculate_atr(self, prices: list) -> float:
        """Calculates Average True Range proxy over the specified period."""
        if len(prices) < self.atr_period + 1:
            return 1.0
        deltas = np.abs(np.diff(prices[-(self.atr_period + 1):]))
        return max(float(np.mean(deltas)), 0.01)

    def calculate_rsi(self, prices: list) -> float:
        """Calculates Relative Strength Index over the specified period."""
        if len(prices) < self.rsi_period + 1:
            return 50.0
        deltas = np.diff(prices[-(self.rsi_period + 1):])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))

    def generate_signal(self, prices: list, current_position: str) -> str:
        """Evaluates entry and exit rules with calibrated anti-peak filters."""
        min_history = max(self.sma_period, self.breakout_period + 1)
        if len(prices) < min_history:
            return "HOLD"

        current_price = prices[-1]
        upper_channel = np.max(prices[-(self.breakout_period + 1):-1])
        lower_channel = np.min(prices[-(self.exit_period + 1):-1])
        
        sma50 = np.mean(prices[-self.sma_period:])
        sma20 = np.mean(prices[-20:])
        atr = self.calculate_atr(prices)
        rsi = self.calculate_rsi(prices)

        # Calibrated Entry Conditions:
        # 1. Price breaks 20-bar upper Donchian channel
        # 2. Bullish alignment: Price > SMA50 AND SMA20 > SMA50
        # 3. Parabolic protection: Price distance from SMA20 does not exceed 4.5 * ATR
        # 4. Healthy momentum: RSI between 50 and 75
        is_breakout = current_price > upper_channel
        is_uptrend = (current_price > sma50) and (sma20 > sma50)
        is_not_parabolic = (current_price - sma20) <= (4.5 * atr)
        is_rsi_valid = 50.0 <= rsi <= 75.0

        if current_position == "NONE" and is_breakout and is_uptrend and is_not_parabolic and is_rsi_valid:
            return "BUY"

        if current_position == "LONG" and current_price < lower_channel:
            return "SELL"

        return "HOLD"