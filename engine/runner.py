from typing import Callable
import logging
import time

class TradingEngine:
    def __init__(self, strategy, broker, throttle=0.5, resolution: str | None = None):
        """
        Trading engine that processes price updates and executes trades.
        
        Args:
            strategy: Strategy instance (manages its own state)
            broker: Broker instance for order execution
            throttle: Minimum time between orders (seconds)
            resolution: Optional resolution filter (e.g., "1m", "5m")
                       If provided, only processes candles matching this resolution
        """
        self.strategy = strategy
        self.broker = broker
        self.last_order_ts = 0
        self.throttle = throttle
        self.resolution = resolution
        self.position_size = 0.0   # size in contracts
        self.position_side = 0  
        self.logger = logging.getLogger("trading_bot")

        self.stats = {
        "trades": 0,
        "wins": 0,
        "losses": 0,
        "total_pnl": 0.0,
        "max_profit": 0.0,
        "max_loss": 0.0,
        }
        self.entry_price = None
  


    async def on_candle(self, candle: dict):
        """
        Process new candle data: update strategy and execute trades if needed.
        
        Signal processing logic:
        - If signal goes from 1 or -1 to 0: Exit current position
        - If signal goes from 0 to 1 or -1: Enter new position
        - If signal goes from 1 to -1 or -1 to 1: Reverse position (exit old, enter new)
        
        Args:
            candle: Dictionary with candlestick data (open, high, low, close, volume, etc.)
        """
        # Filter by resolution if specified
        if self.resolution and candle.get("resolution") != self.resolution:
            return
        
        # Store previous signal before update
        prev_signal = self.strategy.last_signal
        
        # Update strategy and get new signal (pass full candle dict)
        signal = self.strategy.update(candle)

        # Skip if signal hasn't changed
        if signal == self.position_side:
            return

        # Throttle orders
        now = time.time()
        if self.position_side == 0 and signal != 0:
            if now - self.last_order_ts < self.throttle:
                return
            self.last_order_ts = now

        # Get price and symbol from candle for broker
        price = candle.get("close", candle.get("open", 0.0))
        symbol = candle.get("symbol")

        # # Case 1: Exit position (signal goes from 1 or -1 to 0)
        # if prev_signal != 0 and signal == 0:
        #     # Exit long position: sell to close
        #     if prev_signal == 1:
        #         await self.broker.market("sell", size, symbol=symbol, price=price)
        #     # Exit short position: buy to close
        #     elif prev_signal == -1:
        #         await self.broker.market("buy", size, symbol=symbol, price=price)

        # # Case 2: Enter position (signal goes from 0 to 1 or -1)
        # elif prev_signal == 0 and signal != 0:
        #     # Enter long position: buy
        #     if signal == 1:
        #         await self.broker.market("buy", size, symbol=symbol, price=price)
        #     # Enter short position: sell
        #     elif signal == -1:
        #         await self.broker.market("sell", size, symbol=symbol, price=price)

        # # Case 3: Reverse position (signal goes from 1 to -1 or -1 to 1)
        # elif prev_signal != 0 and signal != 0 and signal != prev_signal:
        #     # Reverse from long to short: sell size 2 (size 1 to close long, size 1 to open short)
        #     if prev_signal == 1 and signal == -1:
        #         await self.broker.market("sell", 2*size, symbol=symbol, price=price)
        #     # Reverse from short to long: buy size 2 (size 1 to close short, size 1 to open long)
        #     elif prev_signal == -1 and signal == 1:
        #         await self.broker.market("buy", 2*size, symbol=symbol, price=price)

        # ENTRY from flat
        if self.position_side == 0 and signal != 0:
            size = self._calc_entry_size(price)

            if signal == 1:
                self.logger.info(f"Entering position: Buying {size} of {symbol} at {price}")
                result = await self.broker.market("buy", size, symbol=symbol, price=price, reduce_only=False)
                if result.get("success"):
                    self.entry_price = price
                    self.position_size = size
                    self.position_side = signal
            else:
                self.logger.info(f"Entering position: Selling {size} of {symbol} at {price}")
                result = await self.broker.market("sell", size, symbol=symbol, price=price, reduce_only=False)
                if result.get("success"):
                    self.entry_price = price
                    self.position_size = size
                    self.position_side = signal


        # EXIT to flat
        elif self.position_side != 0 and signal == 0:
            side = "sell" if self.position_side == 1 else "buy"
            if side == "sell":
                self.logger.info(f"Exiting long position: Selling to close {self.position_size} of {symbol} at {price}")
            else:
                self.logger.info(f"Exiting short position: Buying to close {self.position_size} of {symbol} at {price}")
            result = await self.broker.market(side, self.position_size, symbol=symbol, price=price, reduce_only=True)
            if result.get("success"):
                pnl = self._calc_pnl(price)
                self.stats["trades"] += 1
                self.stats["total_pnl"] += pnl
                if pnl > 0:
                    self.stats["wins"] += 1
                    self.stats["max_profit"] = max(self.stats["max_profit"], pnl)
                else:
                    self.stats["losses"] += 1
                    self.stats["max_loss"] = min(self.stats["max_loss"], pnl)
                self.entry_price = None
                self.position_size = 0.0
                self.position_side = 0


        # REVERSE
        elif self.position_side != 0 and signal != 0 and signal != self.position_side:
            exit_side = "sell" if self.position_side == 1 else "buy"
            if exit_side == "sell":
                self.logger.info(f"Exiting long position: Selling to close {self.position_size} of {symbol} at {price}")
            else:
                self.logger.info(f"Exiting short position: Buying to close {self.position_size} of {symbol} at {price}")
            result = await self.broker.market(exit_side, self.position_size, symbol=symbol, price=price, reduce_only=True)
            if result.get("success"):
                pnl = self._calc_pnl(price)
                self.stats["trades"] += 1
                self.stats["total_pnl"] += pnl
                if pnl > 0:
                    self.stats["wins"] += 1
                    self.stats["max_profit"] = max(self.stats["max_profit"], pnl)
                else:
                    self.stats["losses"] += 1
                    self.stats["max_loss"] = min(self.stats["max_loss"], pnl)
                self.entry_price = None

                new_size = self._calc_entry_size(price)
                entry_side = "buy" if signal == 1 else "sell"
                if entry_side == "buy":
                    self.logger.info(f"Entering position: Buying {new_size} of {symbol} at {price}")
                else:
                    self.logger.info(f"Entering position: Selling {new_size} of {symbol} at {price}")
                result = await self.broker.market(entry_side, new_size, symbol=symbol, price=price, reduce_only=False)
                if result.get("success"):
                    self.entry_price = price
                    self.position_size = new_size
                    self.position_side = signal

    def _calc_pnl(self, exit_price: float) -> float:
        return (exit_price - self.entry_price) * self.position_size * self.position_side



    def _calc_entry_size(self, price: float) -> float:
        NOTIONAL = 10.0
        return NOTIONAL / price

    def get_stats(self) -> dict:
        trades = self.stats["trades"]
        wins = self.stats["wins"]
        losses = self.stats["losses"]

        win_rate = (wins / trades * 100) if trades > 0 else 0.0

        return {
            "trades": trades,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "total_pnl": self.stats["total_pnl"],
            "max_profit": self.stats["max_profit"],
            "max_loss": self.stats["max_loss"],
            "open_position": {
                "side": self.position_side,
                "size": self.position_size,
                "entry_price": self.entry_price,
            }
        }



class MultiSymbolEngine:
    """
    Trading engine that handles multiple symbols, maintaining separate strategy state per symbol.
    """
    def __init__(self, strategy_factory: Callable, broker, throttle=0.5, resolution: str | None = None):
        """
        Multi-symbol trading engine.
        
        Args:
            strategy_factory: Callable that returns a new strategy instance (e.g., lambda: RollingReturnStrategy(...))
            broker: Broker instance for order execution
            throttle: Minimum time between orders per symbol (seconds)
            resolution: Optional resolution filter (e.g., "1m", "5m")
        """
        self.strategy_factory = strategy_factory
        self.broker = broker
        self.throttle = throttle
        self.resolution = resolution
        self.engines: dict[str, TradingEngine] = {}
    
    def _get_engine(self, symbol: str) -> TradingEngine:
        """Get or create engine for a symbol."""
        if symbol not in self.engines:
            strategy = self.strategy_factory()
            self.engines[symbol] = TradingEngine(
                strategy=strategy,
                broker=self.broker,
                throttle=self.throttle,
                resolution=self.resolution
            )
        return self.engines[symbol]
    
    async def on_candle(self, candle: dict):
        """
        Process candle for the appropriate symbol's engine.
        
        Args:
            candle: Dictionary with candlestick data (must include 'symbol' key)
        """
        symbol = candle.get("symbol")
        if not symbol:
            return
        
        engine = self._get_engine(symbol)
        await engine.on_candle(candle)


    def get_stats(self) -> dict:
        summary = {
            "total_trades": 0,
            "total_wins": 0,
            "total_losses": 0,
            "total_pnl": 0.0,
            "win_rate": 0.0,
        }

        per_symbol = {}

        for symbol, engine in self.engines.items():
            stats = engine.get_stats()
            per_symbol[symbol] = stats

            summary["total_trades"] += stats["trades"]
            summary["total_wins"] += stats["wins"]
            summary["total_losses"] += stats["losses"]
            summary["total_pnl"] += stats["total_pnl"]

        if summary["total_trades"] > 0:
            summary["win_rate"] = (
                summary["total_wins"] / summary["total_trades"] * 100
            )

        return {
            "summary": summary,
            "per_symbol": per_symbol,
        }
