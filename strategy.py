import numpy as np

class BollingerRSIStrategy:
    """Generates signals using Bollinger Bands, RSI, and an SMA crossover trend filter."""
    
    def __init__(self, bb_period: int = 20, num_std_dev: float = 2.0, 
                 rsi_period: int = 14, rsi_oversold: float = 30.0, 
                 rsi_overbought: float = 70.0, trend_sma_period: int = 50):
        self.bb_period = bb_period
        self.num_std_dev = num_std_dev
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.trend_sma_period = trend_sma_period

    def generate_signal(self, prices: list) -> str:
        if len(prices) < max(self.bb_period, self.rsi_period, self.trend_sma_period):
            return "HOLD"

        current_price = prices[-1]
        
        # Bollinger Bands (20-period)
        window = prices[-self.bb_period:]
        sma = np.mean(window)
        std = np.std(window)
        lower_band = sma - (self.num_std_dev * std)
        upper_band = sma + (self.num_std_dev * std)

        # Macro Trend Filter (50-period SMA)
        trend_sma = np.mean(prices[-self.trend_sma_period:])

        # RSI Calculation
        deltas = np.diff(prices[-(self.rsi_period + 1):])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)

        if avg_loss == 0:
            rsi = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi = 100.0 - (100.0 / (1.0 + rs))

        # BUY: Price dipped below lower band & RSI oversold, BUT 20 SMA > 50 SMA (Uptrend)
        if current_price < lower_band and rsi < self.rsi_oversold and sma > trend_sma:
            return "BUY"

        # SELL: Take profit on upper band breach or overbought RSI
        if current_price > upper_band or rsi > self.rsi_overbought:
            return "SELL"

        return "HOLD"