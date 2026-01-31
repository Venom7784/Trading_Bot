"""
Main script for paper trading - uses PaperBroker instead of real broker.
This allows you to test strategies without risking real money.
"""
import asyncio
import signal
import sys

from config.settings import (
    WS_URL,
    SYMBOLS,
)
from data.webscoket import candlestick_stream
from engine.runner import MultiSymbolEngine
from execution.paper_broker import PaperBroker
from strategy.rolling_return import RollingReturnStrategy


# Global paper broker instance for statistics access
paper_broker: PaperBroker | None = None


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully - print statistics before exiting."""
    if paper_broker:
        print("\n\n[INFO] Shutting down... Printing final statistics:")
        paper_broker.print_statistics()
        # Optionally export trades
        # paper_broker.export_trades("trades.json")
    sys.exit(0)


async def main() -> None:
    """
    Paper trading bot - tests strategies without real money.
    
    Uses PaperBroker to simulate trades and track:
    - Profit and Loss (P&L)
    - Number of trades
    - Win rate
    - Per-symbol statistics
    """
    global paper_broker
    
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Strategy resolution - change this to match your strategy's needs
    strategy_resolution = "1m"
    
    # Strategy factory - creates a new strategy instance per symbol
    def create_strategy():
        return RollingReturnStrategy(window=5, long_th=0.0001, short_th=-0.0001)

    # Initialize paper broker with starting balance
    paper_broker = PaperBroker(initial_balance=10000.0)
    
    print(f"[INFO] Starting PAPER TRADING bot")
    print(f"[INFO] Initial Balance: ${paper_broker.initial_balance:.2f}")
    print(f"[INFO] Symbols ({len(SYMBOLS)}): {SYMBOLS}")
    print(f"[INFO] Resolution: {strategy_resolution}")
    print(f"[INFO] Strategy: {RollingReturnStrategy.__name__}")
    print(f"[INFO] Press Ctrl+C to stop and view statistics\n")

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
            # Debug: Print candle data
            symbol = candle.get("symbol", "UNKNOWN")
            resolution = candle.get("resolution", "UNKNOWN")
            open_price = candle.get("open", 0.0)
            high = candle.get("high", 0.0)
            low = candle.get("low", 0.0)
            close = candle.get("close", 0.0)
            volume = candle.get("volume", 0.0)
            timestamp = candle.get("timestamp", 0)
            
            print(f"[CANDLE] {symbol} | {resolution} | "
                  f"O:{open_price:.2f} H:{high:.2f} L:{low:.2f} C:{close:.2f} | "
                  f"V:{volume:.2f} | TS:{timestamp}")
            
            # Feed candle to engine
            await engine.on_candle(candle)
            
            # Periodically print statistics
            current_time = time.time()
            if current_time - last_stats_print >= stats_interval:
                print(f"\n[STATS] Periodic update ({stats_interval // 60} min interval):")
                paper_broker.print_statistics()
                last_stats_print = current_time
                
        except Exception as e:
            # Log error but continue processing other coins
            symbol = candle.get("symbol", "UNKNOWN")
            print(f"[ERROR] Failed to process candle for {symbol}: {e}")
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
        # Print final statistics
        if paper_broker:
            print("\n[INFO] Final Statistics:")
            paper_broker.print_statistics()
