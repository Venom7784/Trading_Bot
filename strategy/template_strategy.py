"""
Template Strategy File

This is a template for creating new trading strategies.
Copy this file and rename it to your strategy name, then implement your logic.

REQUIREMENTS:
1. Your strategy class must have an `update(candle: dict) -> int` method
2. Your strategy must track `self.last_signal: int` attribute
3. The `update()` method must return: 1 (long), -1 (short), or 0 (flat)
4. No base class inheritance required - just implement the interface!

SIGNAL INTERPRETATION BY TRADING ENGINE:
=========================================
The TradingEngine interprets your signals and executes trades as follows:

Signal Values:
    - 1  = Long position (buy signal)
    - -1 = Short position (sell signal)
    - 0  = Flat/neutral (no position)

Signal Transitions and Trade Execution:
----------------------------------------
1. EXIT POSITION (prev_signal: 1 or -1 → signal: 0)
   - Long to Flat (1 → 0): SELL size 1 (closes long position)
   - Short to Flat (-1 → 0): BUY size 1 (closes short position)

2. ENTER POSITION (prev_signal: 0 → signal: 1 or -1)
   - Flat to Long (0 → 1): BUY size 1 (opens long position)
   - Flat to Short (0 → -1): SELL size 1 (opens short position)

3. REVERSE POSITION (prev_signal: 1 or -1 → signal: -1 or 1)
   - Long to Short (1 → -1): SELL size 2 (closes long + opens short)
   - Short to Long (-1 → 1): BUY size 2 (closes short + opens long)

4. NO CHANGE (prev_signal == signal)
   - No trade executed (e.g., 1 → 1, -1 → -1, 0 → 0)

IMPORTANT NOTES:
- Only signal CHANGES trigger trades
- If your signal stays the same (e.g., 1 → 1), no trade is executed
- Always update self.last_signal before returning from update()
- The engine compares your returned signal with the previous signal

CANDLE DICTIONARY STRUCTURE:
The `candle` dict passed to `update()` contains:
    - close: float          (required) - Closing price
    - open: float            (required) - Opening price
    - high: float            (required) - Highest price
    - low: float             (required) - Lowest price
    - volume: float          (optional) - Trading volume
    - resolution: str        (optional) - Timeframe (e.g., "1m", "5m", "1h")
    - symbol: str            (optional) - Trading symbol (e.g., "BTCUSD")
    - timestamp: int         (optional) - Message timestamp
    - candle_start_time: int (optional) - Candle start timestamp
    - type: str              (optional) - Message type (e.g., "candlestick_1m")

USAGE:
    from strategy.your_strategy import YourStrategy
    
    strategy = YourStrategy(param1=10, param2=20)
    # Use in TradingEngine - it will call update() with candle data
"""

from collections import deque  # Example: useful for rolling windows


class TemplateStrategy:
    """
    Template strategy - replace with your strategy name and description.
    
    This strategy demonstrates the required structure and common patterns.
    """
    
    def __init__(self, param1: float = 10.0, param2: float = 20.0):
        """
        Initialize your strategy with parameters.
        
        Args:
            param1: Example parameter - adjust to your needs
            param2: Example parameter - adjust to your needs
        """
        # REQUIRED: Initialize last_signal attribute
        # This tracks the current signal state: 1 (long), -1 (short), 0 (flat)
        self.last_signal: int = 0
        
        # Store your parameters
        self.param1 = param1
        self.param2 = param2
        
        # Example: Initialize data structures for state management
        # You can use deques, lists, numpy arrays, etc. - whatever fits your needs
        self.price_history = deque(maxlen=100)  # Rolling window of prices
        self.indicators = {}  # Store calculated indicators
        
        # Add any other state variables you need
        # self.some_state = None
    
    def update(self, candle: dict) -> int:
        """
        REQUIRED METHOD: Update strategy state and generate trading signal.
        
        This method is called by TradingEngine for each new candlestick.
        
        Args:
            candle: Dictionary containing candlestick data with keys:
                   - close, open, high, low (required floats)
                   - volume, resolution, symbol, timestamp (optional)
        
        Returns:
            int: Trading signal
                - 1: Long position (buy signal)
                - -1: Short position (sell signal)
                - 0: Flat/neutral (no position)
        
        IMPORTANT:
            - You MUST update self.last_signal before returning
            - You MUST return the signal value
            - The engine uses this to detect signal changes and execute trades
        """
        
        # ============================================================
        # STEP 1: Extract data from candle dictionary
        # ============================================================
        
        # Required fields (always present)
        close = candle["close"]
        open_price = candle["open"]
        high = candle["high"]
        low = candle["low"]
        
        # Optional fields (use .get() with defaults)
        volume = candle.get("volume", 0.0)  # Default to 0 if not present
        resolution = candle.get("resolution", "unknown")  # Timeframe
        symbol = candle.get("symbol", "unknown")  # Trading pair
        timestamp = candle.get("timestamp")  # Message timestamp
        
        # ============================================================
        # STEP 2: Update your internal state
        # ============================================================
        
        # Example: Store price history
        self.price_history.append(close)
        
        # Example: Calculate indicators
        # You can calculate moving averages, RSI, MACD, etc.
        # if len(self.price_history) >= 20:
        #     sma_20 = sum(self.price_history) / len(self.price_history)
        #     self.indicators["sma_20"] = sma_20
        
        # Example: Track price patterns
        # body_size = abs(close - open_price)
        # upper_wick = high - max(close, open_price)
        # lower_wick = min(close, open_price) - low
        
        # ============================================================
        # STEP 3: Implement your trading logic
        # ============================================================
        
        # Example logic patterns (replace with your actual strategy):
        
        # Pattern 1: Simple threshold-based
        # if close > some_threshold:
        #     signal = 1
        # elif close < another_threshold:
        #     signal = -1
        # else:
        #     signal = 0
        
        # Pattern 2: Indicator-based
        # if len(self.price_history) < minimum_data_points:
        #     signal = 0  # Not enough data yet
        # else:
        #     # Calculate your indicators
        #     # Make decision based on indicators
        #     signal = your_logic_here()
        
        # Pattern 3: Pattern recognition
        # if detect_bullish_pattern(candle):
        #     signal = 1
        # elif detect_bearish_pattern(candle):
        #     signal = -1
        # else:
        #     signal = 0
        
        # ============================================================
        # STEP 4: Generate and return signal
        # ============================================================
        
        # TODO: Replace this with your actual signal generation logic
        # For now, this is a placeholder that always returns flat
        signal = 0
        
        # Example: Simple momentum strategy
        # if len(self.price_history) >= 2:
        #     price_change = self.price_history[-1] - self.price_history[-2]
        #     if price_change > self.param1:
        #         signal = 1  # Long on upward momentum
        #     elif price_change < -self.param2:
        #         signal = -1  # Short on downward momentum
        #     else:
        #         signal = 0
        
        # REQUIRED: Update last_signal before returning
        # The TradingEngine uses this to detect signal changes and execute trades
        # Signal transitions are interpreted as:
        #   - 1 or -1 → 0: Exit position
        #   - 0 → 1 or -1: Enter position
        #   - 1 → -1 or -1 → 1: Reverse position (size 2)
        #   - Same signal: No trade
        self.last_signal = signal
        
        # REQUIRED: Return the signal value (1, -1, or 0)
        # This is what the TradingEngine uses to determine what trade to execute
        return signal
    
    # ============================================================
    # OPTIONAL: Helper methods for your strategy
    # ============================================================
    
    def calculate_indicator(self, data: list[float]) -> float:
        """
        Example helper method - add your own helper methods as needed.
        
        You can create methods to:
        - Calculate technical indicators
        - Detect patterns
        - Manage risk
        - Log information
        - etc.
        """
        # Example: Simple moving average
        if not data:
            return 0.0
        return sum(data) / len(data)
    
    def reset(self):
        """
        Optional: Reset strategy state if needed.
        
        Useful for backtesting or restarting the strategy.
        """
        self.last_signal = 0
        self.price_history.clear()
        self.indicators.clear()


# ============================================================
# USAGE EXAMPLE:
# ============================================================
"""
# In main.py or backtest.py:

from strategy.template_strategy import TemplateStrategy

# Create strategy instance
strategy = TemplateStrategy(param1=10.0, param2=20.0)

# Use with TradingEngine
from engine.runner import TradingEngine
from execution.broker import Broker

engine = TradingEngine(strategy, broker, resolution="1m")

# The engine will automatically call strategy.update(candle) for each new candle
"""

