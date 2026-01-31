"""
Main script for paper trading with Max Breakout Short Strategy.
Uses PaperBroker to test the strategy without risking real money.

This strategy:
- Takes SHORT positions when close > rolling 180-candle max
- Exits with 3% target return or 1% stop loss
- Tracks P&L throughout the position lifecycle
"""
import asyncio
import logging
import signal
import sys
from pathlib import Path
from datetime import datetime

from config.settings import (
    WS_URL,
    SYMBOLS,
)
from data.webscoket import candlestick_stream
from engine.runner import MultiSymbolEngine
from execution.paper_broker import PaperBroker
from strategy.max_breakout_short_strategy import MaxBreakoutShortStrategy

# Setup single logger for the application
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = log_dir / f"trading_bot_{timestamp}.log"

logger = logging.getLogger("trading_bot")
logger.setLevel(logging.INFO)
logger.handlers.clear()

# File handler
file_handler = logging.FileHandler(log_file, encoding="utf-8")
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)


# Global paper broker instance for statistics access
paper_broker: PaperBroker | None = None


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully - log statistics before exiting."""
    if paper_broker:
        logger.info("Shutting down... Printing final statistics:")
        paper_broker.print_statistics()
        # Optionally export trades
        # paper_broker.export_trades("trades.json")
    sys.exit(0)


async def main() -> None:
    """
    Paper trading bot for Max Breakout Short Strategy.
    
    Tests the strategy without real money:
    - Tracks P&L per position
    - Monitors win rate
    - Records per-symbol performance
    """
    global paper_broker
    
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Strategy resolution - 1m candles for breakout detection
    strategy_resolution = "1m"
    
    # Strategy factory - creates a new strategy instance per symbol
    def create_strategy():
        return MaxBreakoutShortStrategy(
            lookback_period=1,      # Look back 180 candles for max
            stop_loss_pct=0.01,        # 1% stop loss
            target_return_pct=0.03     # 3% target return
        )

    # Initialize paper broker with starting balance
    paper_broker = PaperBroker(initial_balance=10000.0)
    
    logger.info(f"Starting PAPER TRADING with Max Breakout Short Strategy")
    logger.info(f"Initial Balance: ${paper_broker.initial_balance:.2f}")
    logger.info(f"Symbols ({len(SYMBOLS)}): {SYMBOLS}")
    logger.info(f"Resolution: {strategy_resolution}")
    logger.info(f"Strategy: {MaxBreakoutShortStrategy.__name__}")
    logger.info(f"Lookback: 180 candles | Stop Loss: 1% | Target: 3%")
    logger.info(f"Press Ctrl+C to stop and view statistics")

    # Create multi-symbol engine with paper broker
    engine = MultiSymbolEngine(
        strategy_factory=create_strategy,
        broker=paper_broker,
        resolution=strategy_resolution,
        throttle=0.5
    )

    # Track last statistics print time
    import time
    last_stats_print = time.time()
    stats_interval = 300  # Print stats every 5 minutes

    # Subscribe to all symbols
    # Error handling: if processing one candle fails, continue with the next
    async for candle in candlestick_stream(WS_URL, SYMBOLS, resolutions=[strategy_resolution]):
        try:
            # Extract candle data for logging
            symbol = candle.get("symbol", "UNKNOWN")
            resolution = candle.get("resolution", "UNKNOWN")
            open_price = candle.get("open", 0.0)
            high = candle.get("high", 0.0)
            low = candle.get("low", 0.0)
            close = candle.get("close", 0.0)
            volume = candle.get("volume", 0.0)
            timestamp = candle.get("timestamp", 0)
            
            logger.info(f"{symbol} | {resolution} | "
                  f"O:{open_price:.2f} H:{high:.2f} L:{low:.2f} C:{close:.2f} | "
                  f"V:{volume:.2f} | TS:{timestamp}")
            
            # Feed candle to engine
            await engine.on_candle(candle)
            
            # Periodically print statistics
            current_time = time.time()
            if current_time - last_stats_print >= stats_interval:
                logger.info(f"Periodic update ({stats_interval // 60} min interval):")
                paper_broker.print_statistics()
                logger.info(f"Current Balance: ${paper_broker.balance:.2f}")
                last_stats_print = current_time
                
        except Exception as e:
            # Log error but continue processing other coins
            symbol = candle.get("symbol", "UNKNOWN")
            logger.error(f"Failed to process candle for {symbol}: {e}")
            # Optionally log full traceback for debugging
            # traceback.print_exc()
            continue


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Handle Ctrl+C
        signal_handler(None, None)
    finally:
        # Log final statistics
        if paper_broker:
            logger.info("Final Statistics:")
            paper_broker.print_statistics()
