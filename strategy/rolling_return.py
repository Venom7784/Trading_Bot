from collections import deque


class RollingReturnStrategy:
    """
    Rolling return strategy that combines state management and signal generation.
    
    Tracks rolling percentage returns over a window and generates signals
    when returns exceed thresholds.
    """

    def __init__(self, window: int = 5, long_th: float = 0.1, short_th: float = -0.1):
        self.window = window
        self.long_th = long_th
        self.short_th = short_th
        self.closes = deque(maxlen=window + 1)
        self.pct = deque(maxlen=window)
        self.last_signal: int = 0

    def update(self, candle: dict) -> int:
        """
        Update state with new candle data and generate signal based on rolling return.
        
        Args:
            candle: Dictionary with candlestick data (must have 'close' key)
                   Can also contain: open, high, low, volume, resolution, etc.
            
        Returns:
            Signal: 1 (long), -1 (short), or 0 (flat)
        """
        close = candle["close"]
        
        # Calculate percentage change if we have previous close
        if self.closes:
            prev = self.closes[-1]
            self.pct.append((close - prev) / prev if prev else 0.0)

        self.closes.append(close)

        # Calculate rolling return percentage
        ret_pct = (sum(self.pct) / len(self.pct)) * 100 if self.pct else 0.0

        # Generate signal
        if ret_pct > self.long_th:
            self.last_signal = 1
        elif ret_pct < self.short_th:
            self.last_signal = -1
        else:
            self.last_signal = 0

        return self.last_signal
