import numpy as np

class BollingerRSIStrategy:
    """Mean-reversion strategy with 50 SMA trend regime filter and ATR calculation."""
    
    def __init__(
        self, 
        bb_period: int = 20, 
        num_std_dev: float = 2.0, 
        rsi_period: int = 14, 
        rsi_oversold: float = 30.0, 
        rsi_overbought: float = 70.0, 
        trend_sma_period: int = 50
    ):
        self.bb_period = bb_period
        self.num_std_dev = num_std_dev
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.trend_sma_period = trend_sma_period

    def calculate_atr(self, prices: list, period: int = 14) -> float:
        """Calculates Average True Range (ATR) proxy from close price series."""
        if len(prices) < period + 1:
            return 1.0
        
        # Calculate mean absolute tick-to-tick price deltas
        deltas = np.abs(np.diff(prices[-(period + 1):]))
        atr = float(np.mean(deltas))
        return max(atr, 0.01)  # Guard against zero-volatility divisions

    def generate_signal(self, prices: list) -> str:
        """Generates entry/exit signals filtered by the 50 SMA trend regime."""
        min_required = max(self.bb_period, self.rsi_period, self.trend_sma_period)
        if len(prices) < min_required:
            return "HOLD"

        current_price = prices[-1]

        # Bollinger Bands
        window = prices[-self.bb_period:]
        sma = np.mean(window)
        std = np.std(window)
        lower_band = sma - (self.num_std_dev * std)
        upper_band = sma + (self.num_std_dev * std)

        # Macro Trend Regime Filter
        trend_sma = np.mean(prices[-self.trend_sma_period:])

        # RSI Calculation
        deltas = np.diff(prices[-(self.rsi_period + 1):])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)

        rsi = 100.0 if avg_loss == 0 else 100.0 - (100.0 / (1.0 + (avg_gain / avg_loss)))

        # Signal Logic: Long Dip Buy only in Macro Uptrends (SMA > Trend SMA)
        if current_price < lower_band and rsi < self.rsi_oversold and sma > trend_sma:
            return "BUY"

        # Exit Signal: Price reaches Upper Band or RSI becomes Overbought
        if current_price > upper_band or rsi > self.rsi_overbought:
            return "SELL"

        return "HOLD"