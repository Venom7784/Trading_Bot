import asyncio
from pathlib import Path
from typing import Any, Tuple

import pandas as pd

from engine.runner import TradingEngine
from strategy.rolling_return import RollingReturnStrategy


class DummyBroker:
    """
    Minimal broker drop‑in used for backtesting.
    It just records market orders in memory instead of sending them to an exchange.
    """

    def __init__(self) -> None:
        self.orders: list[dict] = []

    async def market(self, side: str, size: float):
        order = {"side": side, "size": size}
        self.orders.append(order)
        return order


async def run_backtest(
    strategy: Any,
    parquet_path: str,
    price_col: str = "close",
    timestamp_col: str = "timestamp",
    resolution: str = "1m",
) -> Tuple[DummyBroker, Any]:
    """
    Runs a backtest over historical data stored in a parquet file.

    Args:
        strategy: Strategy instance to backtest
        parquet_path: Path to parquet file with historical data
        price_col: Column name for prices (default: 'close')
        timestamp_col: Column name for timestamps (used for sorting, if present)
        resolution: Resolution string (e.g., "1m", "5m") for the candlestick data

    Returns:
        Tuple of (broker, strategy) - broker contains order history, strategy contains final state
    """
    path = Path(parquet_path)
    if not path.is_file():
        raise FileNotFoundError(f"Parquet file not found: {parquet_path}")

    df = pd.read_parquet(path)

    # Ensure sorted in time
    if timestamp_col in df.columns:
        df = df.sort_values(by=timestamp_col)

    broker = DummyBroker()
    engine = TradingEngine(strategy, broker, resolution=resolution)

    # Build full candle dictionary from dataframe row
    for _, row in df.iterrows():
        candle = {
            "close": float(row[price_col]),
            "open": float(row.get("open", row[price_col])),
            "high": float(row.get("high", row[price_col])),
            "low": float(row.get("low", row[price_col])),
            "resolution": resolution,
            "timestamp": int(row.get(timestamp_col, 0)) if timestamp_col in df.columns else None,
        }
        
        # Add volume if present
        if "volume" in df.columns:
            candle["volume"] = float(row["volume"])
        
        await engine.on_candle(candle)

    return broker, strategy


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Backtest rolling‑return strategy on 1m parquet data.")
    parser.add_argument("parquet_path", help="Path to the parquet file with historical 1m data.")
    parser.add_argument("--window", type=int, default=5, help="Rolling window size.")
    parser.add_argument("--long-th", type=float, default=0.1, help="Long threshold (percent).")
    parser.add_argument("--short-th", type=float, default=-0.1, help="Short threshold (percent).")
    parser.add_argument("--price-col", type=str, default="close", help="Column name for prices.")
    parser.add_argument(
        "--timestamp-col",
        type=str,
        default="timestamp",
        help="Column name for timestamps (used for sorting, if present).",
    )
    parser.add_argument(
        "--resolution",
        type=str,
        default="1m",
        help="Resolution of the candlestick data (e.g., '1m', '5m', '1h').",
    )

    args = parser.parse_args()

    # Create strategy instance
    strategy = RollingReturnStrategy(window=args.window, long_th=args.long_th, short_th=args.short_th)

    broker, strategy = asyncio.run(
        run_backtest(
            strategy=strategy,
            parquet_path=args.parquet_path,
            price_col=args.price_col,
            timestamp_col=args.timestamp_col,
            resolution=args.resolution,
        )
    )

    n_trades = len(broker.orders)
    n_longs = sum(1 for o in broker.orders if o["side"] == "buy")
    n_shorts = n_trades - n_longs

    print(f"Trades: {n_trades} (long: {n_longs}, short: {n_shorts})")
    print(f"Final signal: {strategy.last_signal}")


if __name__ == "__main__":
    main()


