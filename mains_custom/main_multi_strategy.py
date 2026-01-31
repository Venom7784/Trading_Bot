"""
Example: Running multiple strategies with different resolutions simultaneously.

This demonstrates how to:
1. Subscribe to multiple candlestick resolutions
2. Route candles to different strategies based on resolution
3. Each strategy can use any fields from the candle dictionary
"""

import asyncio

import aiohttp

from config.settings import (
    API_KEY,
    API_SECRET,
    PRODUCT_ID,
    WS_URL,
    SYMBOL,
)
from data.webscoket import candlestick_stream
from engine.runner import TradingEngine
from execution.broker import Broker
from strategy.rolling_return import RollingReturnStrategy
from strategy.example_strategy import SimpleMovingAverageStrategy


async def main() -> None:
    """
    Run multiple strategies with different resolutions.
    
    Strategy 1: RollingReturnStrategy on 1m candles
    Strategy 2: SimpleMovingAverageStrategy on 5m candles
    """
    
    async with aiohttp.ClientSession(base_url="https://api.delta.exchange") as session:
        broker = Broker(session, API_KEY, API_SECRET, PRODUCT_ID)
        
        # Create strategies
        strategy_1m = RollingReturnStrategy(window=5, long_th=0.1, short_th=-0.1)
        strategy_5m = SimpleMovingAverageStrategy(fast_period=10, slow_period=20)
        
        # Create engines with resolution filters
        engine_1m = TradingEngine(strategy_1m, broker, resolution="1m")
        engine_5m = TradingEngine(strategy_5m, broker, resolution="5m")
        
        # Subscribe to both resolutions
        async for candle in candlestick_stream(WS_URL, SYMBOL, resolutions=["1m", "5m"]):
            # Each engine will filter and process only candles matching its resolution
            await engine_1m.on_candle(candle)
            await engine_5m.on_candle(candle)


if __name__ == "__main__":
    asyncio.run(main())

