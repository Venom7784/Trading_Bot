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
from strategy.rsi_pullback_strategy import RSIPullbackStrategy

# The strategy class and its parameters
STRATEGY_CLASS = RSIPullbackStrategy
STRATEGY_PARAMS = {
    "rsi_period": 14,
    "pullback_5m": 30,
    "pullback_1h": 35,
    "take_profit": 0.015,  # 1.5%
    "stop_loss": -0.005,   # -0.5%
}


# ============================================================================
# ENGINE CONFIGURATION
# ============================================================================
RESOLUTION = "5m"  # Candle resolution for strategy
THROTTLE = 0.5     # Minimum time between orders (seconds)

# ============================================================================
# HISTORICAL DATA CONFIGURATION
# ============================================================================
# Number of days of historical data to feed into the strategy before live trading
DAYS_BACK = 0.5

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
