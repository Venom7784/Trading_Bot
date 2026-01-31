"""
Template Main File

This is a template for setting up and running your trading bot.
Copy this file to main.py and customize it for your strategy.

STRUCTURE:
---------
1. Import your strategy and required modules
2. Configure your strategy parameters
3. Set up broker connection
4. Create TradingEngine with your strategy
5. Subscribe to candlestick data
6. Feed candles to the engine

SIGNAL INTERPRETATION:
---------------------
The TradingEngine automatically interprets your strategy signals:

Signal Values:
    - 1  = Long position (buy signal)
    - -1 = Short position (sell signal)
    - 0  = Flat/neutral (no position)

Signal Transitions:
    - 1/-1 → 0: Exit position (size 1)
    - 0 → 1/-1: Enter position (size 1)
    - 1 ↔ -1: Reverse position (size 2)
    - Same signal: No trade

CONFIGURATION:
-------------
Set your API credentials in config/settings.py or use environment variables:
    - DELTA_API_KEY
    - DELTA_API_SECRET
    - DELTA_PRODUCT_ID
    - DELTA_WS_URL
    - DELTA_SYMBOL

SUPPORTED RESOLUTIONS:
---------------------
["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "12h", "1d", "1w"]
"""

import asyncio

import aiohttp

# ============================================================
# STEP 1: Import Configuration
# ============================================================
from config.settings import (
    API_KEY,
    API_SECRET,
    PRODUCT_ID,
    WS_URL,
    SYMBOL,
)

# ============================================================
# STEP 2: Import Trading Components
# ============================================================
from data.webscoket import candlestick_stream
from engine.runner import TradingEngine
from execution.broker import Broker

# ============================================================
# STEP 3: Import Your Strategy
# ============================================================
# Replace this with your strategy import
# Example:
#   from strategy.your_strategy import YourStrategy
#   from strategy.rolling_return import RollingReturnStrategy
#   from strategy.example_strategy import SimpleMovingAverageStrategy

from strategy.rolling_return import RollingReturnStrategy  # Example import


async def main() -> None:
    """
    Main function that sets up and runs the trading bot.
    
    This function:
    1. Creates your strategy instance with parameters
    2. Sets up broker connection to the exchange
    3. Creates TradingEngine to process signals
    4. Subscribes to candlestick data
    5. Feeds incoming candles to the engine
    
    The engine automatically:
    - Calls strategy.update(candle) for each new candle
    - Detects signal changes
    - Executes trades based on signal transitions
    """
    
    # ============================================================
    # STEP 4: Configure Strategy Parameters
    # ============================================================
    
    # Set the candlestick resolution your strategy needs
    # Supported: "1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "12h", "1d", "1w"
    strategy_resolution = "1m"  # Change this to match your strategy's timeframe
    
    # ============================================================
    # STEP 5: Create Strategy Instance
    # ============================================================
    
    # Create your strategy with your desired parameters
    # The strategy manages its own internal state
    # Example:
    #   strategy = YourStrategy(param1=10, param2=20)
    #   strategy = SimpleMovingAverageStrategy(fast_period=10, slow_period=20)
    
    strategy = RollingReturnStrategy(
        window=5,        # Rolling window size
        long_th=0.1,    # Long threshold (percent)
        short_th=-0.1   # Short threshold (percent)
    )
    
    # ============================================================
    # STEP 6: Set Up Broker and Engine
    # ============================================================
    
    # Create HTTP session for broker API calls
    async with aiohttp.ClientSession(base_url="https://api.delta.exchange") as session:
        
        # Initialize broker with your API credentials
        # The broker handles order execution (buy/sell)
        broker = Broker(
            session=session,
            api_key=API_KEY,
            api_secret=API_SECRET,
            product_id=PRODUCT_ID
        )
        
        # Create trading engine
        # The engine:
        #   - Processes candles and calls strategy.update()
        #   - Detects signal changes
        #   - Executes trades through the broker
        #   - Filters candles by resolution if specified
        engine = TradingEngine(
            strategy=strategy,
            broker=broker,
            resolution=strategy_resolution,  # Only process candles matching this resolution
            throttle=0.5  # Optional: minimum seconds between orders (default: 0.5)
        )
        
        # ============================================================
        # STEP 7: Subscribe to Candlestick Data
        # ============================================================
        
        print(f"[INFO] Starting bot with strategy: {strategy.__class__.__name__}")
        print(f"[INFO] Resolution: {strategy_resolution}")
        print(f"[INFO] Symbol: {SYMBOL}")
        print(f"[INFO] Waiting for candlestick data...")
        
        # Subscribe to candlestick stream
        # You can subscribe to multiple resolutions simultaneously
        # Example: resolutions=["1m", "5m", "1h"]
        async for candle in candlestick_stream(
            ws_url=WS_URL,
            symbol=SYMBOL,
            resolutions=[strategy_resolution]  # List of resolutions to subscribe to
        ):
            # Each candle is a dictionary with:
            #   - open, high, low, close (required floats)
            #   - volume, resolution, symbol, timestamp (optional)
            
            # Feed candle to engine
            # The engine will:
            #   1. Filter by resolution (if specified)
            #   2. Call strategy.update(candle)
            #   3. Detect signal changes
            #   4. Execute trades if signal changed
            await engine.on_candle(candle)


# ============================================================
# STEP 8: Run the Bot
# ============================================================
if __name__ == "__main__":
    """
    Entry point for the trading bot.
    
    Run this file with:
        python main.py
    
    Or as a module:
        python -m main
    """
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[INFO] Bot stopped by user")
    except Exception as e:
        print(f"[ERROR] Bot crashed: {e}")
        raise


# ============================================================
# ADVANCED: Multiple Strategies Example
# ============================================================
"""
If you want to run multiple strategies with different resolutions:

async def main_multi_strategy():
    async with aiohttp.ClientSession(base_url="https://api.delta.exchange") as session:
        broker = Broker(session, API_KEY, API_SECRET, PRODUCT_ID)
        
        # Create multiple strategies
        strategy_1m = RollingReturnStrategy(window=5, long_th=0.1, short_th=-0.1)
        strategy_5m = SimpleMovingAverageStrategy(fast_period=10, slow_period=20)
        
        # Create engines with different resolutions
        engine_1m = TradingEngine(strategy_1m, broker, resolution="1m")
        engine_5m = TradingEngine(strategy_5m, broker, resolution="5m")
        
        # Subscribe to both resolutions
        async for candle in candlestick_stream(WS_URL, SYMBOL, resolutions=["1m", "5m"]):
            # Each engine filters and processes only its resolution
            await engine_1m.on_candle(candle)
            await engine_5m.on_candle(candle)
"""

