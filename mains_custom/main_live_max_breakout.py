"""
Main script for LIVE trading with Max Breakout Short Strategy.
Uses real Broker to execute trades with real money.

This strategy:
- Takes SHORT positions when close > rolling 180-candle max
- Exits with 3% target return or 1% stop loss
- Tracks P&L throughout the position lifecycle
"""
import asyncio
import signal
import sys
import aiohttp

from config.settings import (
    API_KEY,
    API_SECRET,
    PRODUCT_ID,
    WS_URL,
    SYMBOLS,
)
from data.webscoket import candlestick_stream
from engine.runner import MultiSymbolEngine
from execution.broker import Broker
from strategy.max_breakout_short_strategy import MaxBreakoutShortStrategy
from utils.logger import setup_strategy_logger

# Initialize logger
logger = setup_strategy_logger(strategy_instance="main_live_max_breakout")

# Global broker instance for statistics access (if needed)
broker = None

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    logger.info("\n[INFO] Shutting down...")
    sys.exit(0)

async def main() -> None:
    """
    LIVE trading bot for Max Breakout Short Strategy.
    Executes trades with real money using Broker.
    """
    global broker
    signal.signal(signal.SIGINT, signal_handler)
    strategy_resolution = "1m"

    def create_strategy():
        return MaxBreakoutShortStrategy(
            lookback_period=1,      # Look back 180 candles for max
            stop_loss_pct=0.01,     # 1% stop loss
            target_return_pct=0.03  # 3% target return
        )

    async with aiohttp.ClientSession(base_url="https://api.delta.exchange") as session:
        broker = Broker(session, API_KEY, API_SECRET, PRODUCT_ID)
        logger.info(f"[INFO] Starting LIVE TRADING with Max Breakout Short Strategy")
        logger.info(f"[INFO] Symbols ({len(SYMBOLS)}): {SYMBOLS}")
        logger.info(f"[INFO] Resolution: {strategy_resolution}")
        logger.info(f"[INFO] Strategy: {MaxBreakoutShortStrategy.__name__}")
        logger.info(f"[INFO] Lookback: 180 candles | Stop Loss: 1% | Target: 3%")
        logger.info(f"[INFO] Press Ctrl+C to stop\n")

        engine = MultiSymbolEngine(
            strategy_factory=create_strategy,
            broker=broker,
            resolution=strategy_resolution,
            throttle=0.5
        )

        import time
        last_stats_print = time.time()
        stats_interval = 300  # Print stats every 5 minutes

        async for candle in candlestick_stream(WS_URL, SYMBOLS, resolutions=[strategy_resolution]):
            try:
                symbol = candle.get("symbol", "UNKNOWN")
                resolution = candle.get("resolution", "UNKNOWN")
                open_price = candle.get("open", 0.0)
                high = candle.get("high", 0.0)
                low = candle.get("low", 0.0)
                close = candle.get("close", 0.0)
                volume = candle.get("volume", 0.0)
                timestamp = candle.get("timestamp", 0)
                logger.info(f"[CANDLE] {symbol} | {resolution} | "
                            f"O:{open_price:.2f} H:{high:.2f} L:{low:.2f} C:{close:.2f} | "
                            f"V:{volume:.2f} | TS:{timestamp}")
                await engine.on_candle(candle)
                current_time = time.time()
                if current_time - last_stats_print >= stats_interval:
                    logger.info(f"\n[STATS] Periodic update ({stats_interval // 60} min interval)")
                    stats = engine.get_stats()
                    logger.info(f"Statistics: {stats}")
                    last_stats_print = current_time
            except Exception as e:
                symbol = candle.get("symbol", "UNKNOWN")
                logger.error(f"[ERROR] Failed to process candle for {symbol}: {e}")
                continue

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        signal_handler(None, None)
