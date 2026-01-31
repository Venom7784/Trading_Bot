"""
Basic configuration for the trading bot.

Fill in your real credentials and instruments here or,
preferably, load them from environment variables.
"""

import os

# REST trading credentials
API_KEY: str = os.getenv("DELTA_API_KEY", "")
API_SECRET: str = os.getenv("DELTA_API_SECRET", "")
PRODUCT_ID: str = os.getenv("DELTA_PRODUCT_ID", "ETHUSD")

# WebSocket market data configuration
WS_URL: str = os.getenv("DELTA_WS_URL", "wss://socket.india.delta.exchange")
SYMBOL: str = os.getenv("DELTA_SYMBOL", "ETHUSD")

# Multiple symbols support - can be a comma-separated string or list
# Example: "BTCUSD,ETHUSD,SOLUSD" or ["BTCUSD", "ETHUSD", "SOLUSD"]
# Default symbols if DELTA_SYMBOLS env var is not set
DEFAULT_SYMBOLS = ["ETHUSD", "BTCUSD"]

SYMBOLS_ENV = os.getenv("DELTA_SYMBOLS", "")
if SYMBOLS_ENV:
    # Handle string (comma-separated) from environment variable
    if isinstance(SYMBOLS_ENV, str):
        SYMBOLS: list[str] = [s.strip() for s in SYMBOLS_ENV.split(",") if s.strip()]
    else:
        SYMBOLS: list[str] = [SYMBOL]
else:
    # Use default symbols list
    SYMBOLS: list[str] = DEFAULT_SYMBOLS

# Debug: Print what symbols are being used (can be removed later)
if __name__ != "__main__":  # Only print when imported, not when run directly
    import sys
    if "pytest" not in sys.modules:  # Don't print during tests
        print(f"[CONFIG] Using symbols: {SYMBOLS} (from {'DELTA_SYMBOLS env var' if SYMBOLS_ENV else 'default SYMBOL config'})")
