from collections import defaultdict
from datetime import datetime
from typing import Optional
import json
import logging

class PaperBroker:
    """
    Paper trading broker that simulates trades without real money.
    Tracks positions, P&L, and trade statistics per symbol.
    """
    
    def __init__(self, initial_balance: float = 10000.0):
        """
        Initialize paper broker with starting balance.
        
        Args:
            initial_balance: Starting capital for paper trading (default: $10,000)
        """
        self.initial_balance = initial_balance
        self.balance = initial_balance
        
        # Position tracking per symbol: {symbol: {"side": "long"/"short", "size": float, "entry_price": float}}
        self.positions: dict[str, dict] = {}
        
        # Trade history: list of completed trades
        self.trade_history: list[dict] = []
        
        # Statistics per symbol
        self.stats: dict[str, dict] = defaultdict(lambda: {
            "trades": 0,
            "wins": 0,
            "losses": 0,
            "total_pnl": 0.0,
            "max_profit": 0.0,
            "max_loss": 0.0,
        })
        
        # Overall statistics
        self.total_trades = 0
        self.total_wins = 0
        self.total_losses = 0
        self.total_pnl = 0.0
        
        # Initialize logger
        self.logger = logging.getLogger("trading_bot")
        
    async def market(self, side: str, size: float, symbol: Optional[str] = None, price: Optional[float] = None, reduce_only: bool = False):
        """
        Execute a market order (paper trade).
        
        Args:
            side: "buy" or "sell"
            size: Order size
            symbol: Trading symbol (required for multi-symbol trading)
            price: Current market price (if not provided, uses last known price)
            reduce_only: If True, only close/reduce positions, don't open new ones
        
        Returns:
            Dictionary with order execution details
        """
        if symbol is None:
            raise ValueError("Symbol is required for paper trading")
        
        if price is None:
            raise ValueError("Price is required for paper trading")
        
        side = side.lower()
        if side not in ["buy", "sell"]:
            raise ValueError(f"Invalid side: {side}. Must be 'buy' or 'sell'")
        
        current_position = self.positions.get(symbol)
        pnl = 0.0
        success = False
        
        # Execute the trade
        if side == "buy":
            # Buying: opening long or closing short
            if current_position and current_position["side"] == "short":
                # Closing short position
                pnl = self._close_position(symbol, price, size, "short")
                success = True
            elif not reduce_only:
                # Opening long position (or increasing long) - only if not reduce_only
                self._open_position(symbol, "long", size, price)
                success = True
        else:  # sell
            # Selling: opening short or closing long
            if current_position and current_position["side"] == "long":
                # Closing long position
                pnl = self._close_position(symbol, price, size, "long")
                success = True
            elif not reduce_only:
                # Opening short position (or increasing short) - only if not reduce_only
                self._open_position(symbol, "short", size, price)
                success = True
        
        # Record trade if position was closed
        if pnl != 0.0:
            trade_record = {
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "side": "close",
                "size": size,
                "price": price,
                "pnl": pnl,
            }
            self.trade_history.append(trade_record)
            self._update_stats(symbol, pnl)
        
        return {
            "success": success,
            "status": "filled" if success else "rejected",
            "side": side,
            "size": size,
            "price": price,
            "symbol": symbol,
            "pnl": pnl if pnl != 0.0 else None,
        }
    
    def _open_position(self, symbol: str, side: str, size: float, price: float):
        """Open or increase a position."""
        if symbol in self.positions:
            # Increase existing position
            pos = self.positions[symbol]
            if pos["side"] == side:
                # Same direction - increase size (weighted average entry price)
                total_value = pos["entry_price"] * pos["size"] + price * size
                pos["size"] += size
                pos["entry_price"] = total_value / pos["size"]
                self.logger.info(f"[POSITION] {symbol}: Increased {side.upper()} position | Size: {pos['size']:.2f} | Entry: ${pos['entry_price']:.2f}")
            else:
                # Opposite direction - reduce or reverse
                if size >= pos["size"]:
                    # Reversing position
                    remaining_size = size - pos["size"]
                    old_side = pos["side"]
                    self.positions[symbol] = {
                        "side": side,
                        "size": remaining_size,
                        "entry_price": price,
                    }
                    self.logger.info(f"[POSITION] {symbol}: REVERSED {old_side.upper()} → {side.upper()} | Size: {remaining_size:.2f} | Entry: ${price:.2f}")
                else:
                    # Reducing position
                    pos["size"] -= size
                    self.logger.info(f"[POSITION] {symbol}: Reduced {pos['side'].upper()} position | Remaining Size: {pos['size']:.2f}")
        else:
            # New position
            self.positions[symbol] = {
                "side": side,
                "size": size,
                "entry_price": price,
            }
            self.logger.info(f"[POSITION] {symbol}: ENTERED {side.upper()} | Size: {size:.2f} | Entry: ${price:.2f}")
    
    def _close_position(self, symbol: str, price: float, size: float, side: str) -> float:
        """
        Close a position and calculate P&L.
        
        Returns:
            Realized P&L
        """
        if symbol not in self.positions:
            return 0.0
        
        pos = self.positions[symbol]
        if pos["side"] != side:
            # Trying to close wrong side - treat as opening opposite position
            self._open_position(symbol, "short" if side == "long" else "long", size, price)
            return 0.0
        
        # Calculate P&L
        entry_price = pos["entry_price"]
        close_size = min(size, pos["size"])
        
        if side == "long":
            # Long: profit when exit price > entry price
            pnl = (price - entry_price) * close_size
        else:  # short
            # Short: profit when exit price < entry price
            pnl = (entry_price - price) * close_size
        
        # Update position
        pos["size"] -= close_size
        was_fully_closed = pos["size"] <= 0
        
        if was_fully_closed:
            # Position fully closed
            del self.positions[symbol]
            pnl_sign = "+" if pnl >= 0 else ""
            self.logger.info(f"[POSITION] {symbol}: EXITED {side.upper()} | Entry: ${entry_price:.2f} | Exit: ${price:.2f} | P&L: {pnl_sign}${pnl:.2f} | Balance: ${self.balance:.2f}")
        else:
            # Partially closed
            self.logger.info(f"[POSITION] {symbol}: Partially closed {side.upper()} | Remaining Size: {pos['size']:.2f} | P&L: ${pnl:.2f}")
        
        # Update balance
        self.balance += pnl
        
        return pnl
    
    def _update_stats(self, symbol: str, pnl: float):
        """Update statistics for a symbol."""
        stats = self.stats[symbol]
        stats["trades"] += 1
        stats["total_pnl"] += pnl
        
        if pnl > 0:
            stats["wins"] += 1
            stats["max_profit"] = max(stats["max_profit"], pnl)
        elif pnl < 0:
            stats["losses"] += 1
            stats["max_loss"] = min(stats["max_loss"], pnl)
        
        # Update overall stats
        self.total_trades += 1
        self.total_pnl += pnl
        if pnl > 0:
            self.total_wins += 1
        elif pnl < 0:
            self.total_losses += 1
    
    def get_unrealized_pnl(self, symbol: str, current_price: float) -> float:
        """Calculate unrealized P&L for a symbol's current position."""
        if symbol not in self.positions:
            return 0.0
        
        pos = self.positions[symbol]
        entry_price = pos["entry_price"]
        size = pos["size"]
        
        if pos["side"] == "long":
            return (current_price - entry_price) * size
        else:  # short
            return (entry_price - current_price) * size
    
    def get_total_unrealized_pnl(self, symbol_prices: dict[str, float]) -> float:
        """Calculate total unrealized P&L across all positions."""
        total = 0.0
        for symbol, pos in self.positions.items():
            if symbol in symbol_prices:
                total += self.get_unrealized_pnl(symbol, symbol_prices[symbol])
        return total
    
    def get_statistics(self, symbol: Optional[str] = None) -> dict:
        """
        Get trading statistics.
        
        Args:
            symbol: If provided, returns stats for that symbol only. Otherwise returns overall stats.
        
        Returns:
            Dictionary with statistics
        """
        if symbol:
            stats = self.stats.get(symbol, {})
            win_rate = (stats["wins"] / stats["trades"] * 100) if stats["trades"] > 0 else 0.0
            return {
                "symbol": symbol,
                "trades": stats["trades"],
                "wins": stats["wins"],
                "losses": stats["losses"],
                "win_rate": win_rate,
                "total_pnl": stats["total_pnl"],
                "max_profit": stats["max_profit"],
                "max_loss": stats["max_loss"],
            }
        else:
            win_rate = (self.total_wins / self.total_trades * 100) if self.total_trades > 0 else 0.0
            return {
                "total_trades": self.total_trades,
                "total_wins": self.total_wins,
                "total_losses": self.total_losses,
                "win_rate": win_rate,
                "total_pnl": self.total_pnl,
                "initial_balance": self.initial_balance,
                "current_balance": self.balance,
                "total_return": ((self.balance - self.initial_balance) / self.initial_balance * 100) if self.initial_balance > 0 else 0.0,
                "open_positions": len(self.positions),
            }
    
    def print_statistics(self, symbol: Optional[str] = None):
        """Print formatted statistics."""
        stats = self.get_statistics(symbol)
        logger = logging.getLogger("trading_bot")

        if symbol:
            logger.info("=== Statistics for %s ===", symbol)
            logger.info("Trades: %d", stats['trades'])
            logger.info("Wins: %d | Losses: %d", stats['wins'], stats['losses'])
            logger.info("Win Rate: %.2f%%", stats['win_rate'])
            logger.info("Total P&L: $%.2f", stats['total_pnl'])
            logger.info("Max Profit: $%.2f | Max Loss: $%.2f", stats['max_profit'], stats['max_loss'])
        else:
            logger.info("=== Overall Paper Trading Statistics ===")
            logger.info("Total Trades: %d", stats['total_trades'])
            logger.info("Wins: %d | Losses: %d", stats['total_wins'], stats['total_losses'])
            logger.info("Win Rate: %.2f%%", stats['win_rate'])
            logger.info("Total P&L: $%.2f", stats['total_pnl'])
            logger.info("Initial Balance: $%.2f", stats['initial_balance'])
            logger.info("Current Balance: $%.2f", stats['current_balance'])
            logger.info("Total Return: %.2f%%", stats['total_return'])
            logger.info("Open Positions: %d", stats['open_positions'])

            # Print per-symbol stats if there are any
            if self.stats:
                logger.info("=== Per-Symbol Statistics ===")
                for sym, sym_stats in sorted(self.stats.items(), key=lambda x: x[1]["total_pnl"], reverse=True):
                    if sym_stats["trades"] > 0:
                        win_rate = (sym_stats["wins"] / sym_stats["trades"] * 100) if sym_stats["trades"] > 0 else 0.0
                        logger.info(
                            "%s: %d trades, %dW/%dL (%.1f%%), P&L: $%.2f",
                            sym,
                            sym_stats['trades'],
                            sym_stats['wins'],
                            sym_stats['losses'],
                            win_rate,
                            sym_stats['total_pnl']
                        )
    
    def get_positions(self) -> dict:
        """Get all open positions."""
        return self.positions.copy()
    
    def export_trades(self, filename: str):
        """Export trade history to JSON file."""
        with open(filename, 'w') as f:
            json.dump({
                "trade_history": self.trade_history,
                "statistics": {sym: self.get_statistics(sym) for sym in self.stats.keys()},
                "overall_stats": self.get_statistics(),
            }, f, indent=2)
        print(f"[INFO] Trade history exported to {filename}")
