"""
Trading configuration - Controls which broker and strategy to use.
Edit this file to switch between different brokers and strategies without modifying main.py.
"""

from typing import Callable, Any

# ============================================================================
# BROKER CONFIGURATION
# ============================================================================
# Choose which broker to use: "paper" or "live"
BROKER_TYPE = "paper"

# Paper broker settings
PAPER_BROKER_CONFIG = {
    "initial_balance": 10000.0,
}

# Live broker settings (not implemented yet)
LIVE_BROKER_CONFIG = {
    # Configure live broker parameters here
}

# ============================================================================
# STRATEGY CONFIGURATION
# ============================================================================
# Strategy class to use - import and reference the class
from strategy.rolling_return import RollingReturnStrategy

# The strategy class and its parameters
STRATEGY_CLASS = RollingReturnStrategy
STRATEGY_PARAMS = {
    "window": 5,        # Look back 180 candles for max
    "long_th": 0.1,       # 1% stop loss
    "short_th":-0.1,   # 3% target return
}

# ============================================================================
# ENGINE CONFIGURATION
# ============================================================================
RESOLUTION = "1m"  # Candle resolution for strategy
THROTTLE = 0.5     # Minimum time between orders (seconds)

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_TO_FILE = True
LOG_TO_CONSOLE = True

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def get_broker_factory() -> Callable:
    """Returns a factory function that creates a broker instance."""
    if BROKER_TYPE == "paper":
        from execution.paper_broker import PaperBroker
        return lambda: PaperBroker(**PAPER_BROKER_CONFIG)
    else:
        raise ValueError(f"Unknown broker type: {BROKER_TYPE}")


def get_strategy_factory() -> Callable:
    """Returns a factory function that creates a new strategy instance."""
    return lambda: STRATEGY_CLASS(**STRATEGY_PARAMS)
