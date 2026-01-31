"""
Example strategy to demonstrate the plug-and-play architecture.

To create a new strategy:
1. Create a class with an update(candle: dict) -> int method
2. Manage your own state internally
3. Track last_signal attribute (1 for long, -1 for short, 0 for flat)
4. Return the signal from update()

The candle dict contains: open, high, low, close, volume (optional), 
resolution, symbol, timestamp, candle_start_time, type

No base class required - just implement the interface!
"""

from collections import deque


class SimpleMovingAverageStrategy:
    """
    Example: Simple moving average crossover strategy.
    
    Goes long when price crosses above SMA, short when below.
    Uses close price from the candle dictionary.
    """

    def __init__(self, fast_period: int = 10, slow_period: int = 20):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.prices = deque(maxlen=slow_period)
        self.last_signal: int = 0

    def update(self, candle: dict) -> int:
        """
        Update with new candle data and generate signal based on SMA crossover.
        
        Args:
            candle: Dictionary with candlestick data (must have 'close' key)
        """
        close = candle["close"]
        self.prices.append(close)

        # Need enough data for both SMAs
        if len(self.prices) < self.slow_period:
            self.last_signal = 0
            return 0

        # Calculate fast and slow SMAs
        fast_sma = sum(list(self.prices)[-self.fast_period:]) / self.fast_period
        slow_sma = sum(self.prices) / len(self.prices)

        # Generate signal
        if fast_sma > slow_sma:
            self.last_signal = 1  # Long
        elif fast_sma < slow_sma:
            self.last_signal = -1  # Short
        else:
            self.last_signal = 0  # Flat

        return self.last_signal

