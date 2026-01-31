"""
Max Breakout Short Strategy

This strategy implements a breakout-based short trading approach:
- Looks for the max close price in the past 180 candles (shifted by 1)
- Takes a SHORT position (-1 signal) when current close > max of past 180 candles
- Exits the position when:
  1. Stop loss is hit (1% loss from entry price)
  2. Target return is achieved (3% profit from entry price)
- Tracks PnL and percentage return throughout the position

SIGNAL INTERPRETATION:
- 1: Long position (not used in this strategy)
- -1: Short position (entered when close > rolling 180-candle max)
- 0: Flat/neutral (exit due to stop loss or target hit)

Requirements met:
✓ update(candle: dict) -> int method
✓ Tracks last_signal attribute
✓ Returns: 1 (not used), -1 (short), or 0 (flat)
✓ Tracks PnL and % return
✓ 1% stop loss, 3% target return
"""

from collections import deque


class MaxBreakoutShortStrategy:
    """
    Breakout Short Strategy with Risk Management.
    
    Entry: Takes SHORT position when close > rolling 180-candle max (shifted by 1)
    Exit: When stop loss (1%) or target return (3%) is hit
    Risk Management: Tracks entry price and PnL
    """

    def __init__(
        self,
        lookback_period: int = 1,
        stop_loss_pct: float = 1.0,
        target_return_pct: float = 3.0
    ):
        """
        Initialize the strategy.
        
        Args:
            lookback_period: Number of candles to look back for max (default: 180)
            stop_loss_pct: Stop loss percentage (default: 1%)
            target_return_pct: Target return percentage (default: 3%)
        """
        # REQUIRED: Track the current signal state
        self.last_signal: int = 0
        
        # Strategy parameters
        self.lookback_period = lookback_period
        self.stop_loss_pct = stop_loss_pct
        self.target_return_pct = target_return_pct
        
        # Price history to calculate rolling max
        self.price_history = deque(maxlen=lookback_period+1)
        
        # Position tracking for risk management
        self.entry_price: float = None  # Entry price when short is opened
        self.pnl: float = 0.0  # Current unrealized PnL
        self.pnl_pct: float = 0.0  # Current unrealized PnL percentage
        self.in_position: bool = False  # Whether we're currently in a short position
        
        # Statistics
        self.total_trades: int = 0
        self.winning_trades: int = 0
        self.losing_trades: int = 0

    def update(self, candle: dict) -> int:
        """
        Update strategy state and generate trading signal.
        
        Args:
            candle: Dictionary containing candlestick data
                   Must have: close, open, high, low
                   Optional: volume, resolution, symbol, timestamp
        
        Returns:
            int: Trading signal
                - -1: SHORT position (entry signal)
                - 0: FLAT/neutral (exit signal or no position)
                - 1: LONG position (not used in this strategy)
        """
        
        # ============================================================
        # STEP 1: Extract data from candle
        # ============================================================
        close = candle["close"]
        
        # Optional data for logging/debugging
        symbol = candle.get("symbol", "UNKNOWN")
        timestamp = candle.get("timestamp")
        resolution = candle.get("resolution", "1m")
        
        # ============================================================
        # STEP 2: Update price history
        # ============================================================
        self.price_history.append(close)
        # ============================================================
        # STEP 3: Check if we're in a position and need to exit
        # ============================================================
        if self.in_position and self.entry_price is not None:
            # Calculate unrealized PnL for a SHORT position
            # For short: profit when price goes DOWN (entry - current)
            self.pnl_pct = (self.entry_price - close)/100
            # Check if target return is hit (3% profit)
            if self.pnl_pct >= self.target_return_pct:
                signal = 0  # Exit position (target hit)
                self._exit_position("TARGET_HIT", close)
                self.last_signal = signal
                return signal
            
            # Check if stop loss is hit (1% loss)
            if self.pnl_pct <= -self.stop_loss_pct:
                signal = 0  # Exit position (stop loss)
                self._exit_position("STOP_LOSS", close)
                self.last_signal = signal
                return signal
            
            # Still in position, no exit condition met
            self.last_signal = -1
            return -1
        
        # ============================================================
        # STEP 4: Check entry condition if NOT in position
        # ============================================================
        # [DEBUG] Log entry condition check
        
        if not self.in_position and len(self.price_history) > self.lookback_period:
            # Get max of past 180 candles (excluding current), shifted by 1
            historical_prices = list(self.price_history)[:-1]  # Exclude current
            rolling_max = max(historical_prices) if historical_prices else 0
            
            # [DEBUG] Log entry check details
            
            # Entry condition: current close > rolling max of past 180
            if close > rolling_max:
                # Enter SHORT position
                self.entry_price = close
                self.in_position = True
                self.pnl = 0.0
                self.pnl_pct = 0.0
                self.total_trades += 1
                
                
                signal = -1  # SHORT signal
                self.last_signal = signal
                return signal
        
        # ============================================================
        # STEP 5: No position and no entry signal
        # ============================================================
        self.last_signal = 0
        return 0
    
    # ============================================================
    # HELPER METHODS
    # ============================================================
    
    def _exit_position(self, exit_reason: str, exit_price: float) -> None:
        """
        Handle position exit and update statistics.
        
        Args:
            exit_reason: Reason for exit ("TARGET_HIT" or "STOP_LOSS")
            exit_price: Price at which position was exited
        """
        if not self.in_position or self.entry_price is None:
            return
        
        # Update statistics
        final_pnl_pct = (self.entry_price - exit_price) / self.entry_price * 100
        
        if final_pnl_pct > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1
        
        # Reset position
        self.entry_price = None
        self.in_position = False
        self.pnl = 0.0
        self.pnl_pct = 0.0
    
    def get_stats(self) -> dict:
        """
        Get strategy statistics.
        
        Returns:
            Dictionary with strategy performance metrics
        """
        win_rate = (
            (self.winning_trades / self.total_trades * 100)
            if self.total_trades > 0
            else 0.0
        )
        
        return {
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate": win_rate,
            "current_pnl": self.pnl,
            "current_pnl_pct": self.pnl_pct,
            "in_position": self.in_position,
        }
    
    def reset(self) -> None:
        """
        Reset strategy state for backtesting or restarting.
        """
        self.last_signal = 0
        self.price_history.clear()
        self.entry_price = None
        self.pnl = 0.0
        self.pnl_pct = 0.0
        self.in_position = False
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
