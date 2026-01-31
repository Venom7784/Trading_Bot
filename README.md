# Algorithmic Trading Bot

A modern, asynchronous trading bot built in Python for executing automated trading strategies on cryptocurrency markets. Features support for multiple strategies, paper trading simulation, and live trading capabilities.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [How It Works](#how-it-works)
- [Usage](#usage)
- [Strategies](#strategies)
- [Project Structure](#project-structure)
- [Advanced Usage](#advanced-usage)
- [Troubleshooting](#troubleshooting)

## Overview

This trading bot is built on a **modular architecture** where:

- **Main Entry Point** (`main.py`): Universal entry point that never needs editing
- **Configuration-Driven**: All behavior is controlled through `config/trading_config.py`
- **Strategy System**: Plug-and-play trading strategies with automatic instantiation
- **Multiple Brokers**: Support for paper trading and live trading
- **Async-First**: Built with Python `asyncio` for high-performance concurrent operations
- **Real-Time Data**: WebSocket connection to market data feeds

IMPORTANT: This bot is implemented to use the Delta Exchange API. Live trading and REST/API actions expect Delta Exchange API credentials (API key and secret) and are not compatible with other exchanges' key formats or endpoints.

## Features

✅ **Multiple Trading Strategies**
- Rolling Return Strategy
- Max Breakout Short Strategy  
- Extensible template for custom strategies

✅ **Paper Trading**
- Simulated trading with configurable initial balance
- Full P&L tracking and statistics per symbol
- Risk management with stop loss and take profit

✅ **Live Trading** 
- Real broker integration for executing trades with real money
- Secure API credential handling via environment variables
- Position and balance tracking
Note: Live trading currently supports Delta Exchange only; provide Delta API key/secret.

✅ **Multi-Symbol Support**
- Trade multiple instruments simultaneously
- Separate strategy instances per symbol
- Concurrent position management

✅ **Comprehensive Logging**
- Configurable log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- File and console output options
- Timestamped log files

✅ **WebSocket Real-Time Data**
- Async candlestick streaming
- Multiple resolution support (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d, 1w)
- Automatic reconnection handling

## Installation

### Prerequisites

- Python 3.11 or 3.12
- pip or uv (recommended)

### Step 1: Clone or Download the Project

```bash
cd bot
```

### Step 2: Install Dependencies

Using `uv` (recommended for speed):

```bash
uv sync
```

Or using pip:

```bash
pip install -r requirements.txt
```

The required packages are:
- `websockets` - WebSocket client for market data
- `aiohttp` - Async HTTP client for API calls
- `pandas` - Data manipulation (for backtesting)

### Step 3: Set Environment Variables

Create a `.env` file or export environment variables for your broker credentials:

```bash
export DELTA_API_KEY="your_api_key"
export DELTA_API_SECRET="your_api_secret"
export DELTA_PRODUCT_ID="ETHUSD"
export DELTA_WS_URL="wss://socket.india.delta.exchange"
export DELTA_SYMBOLS="BTCUSD,ETHUSD"
```

Note: The variables above must contain credentials issued by Delta Exchange. The bot accepts only Delta API keys and secrets for live trading; other exchanges' credentials will not work.

See the Delta Exchange API documentation for details and credential setup: [Delta Exchange API docs](https://docs.delta.exchange/#introduction).

Or set them in `config/settings.py` (not recommended for production):

```python
API_KEY = "your_api_key"
API_SECRET = "your_api_secret"
```

## Configuration

All trading behavior is controlled through **`config/trading_config.py`**. You should NEVER need to edit `main.py`.

### Basic Configuration

```python
# Choose broker type: "paper" or "live"
BROKER_TYPE = "paper"

# Paper broker starting balance
PAPER_BROKER_CONFIG = {
    "initial_balance": 10000.0,
}

# Strategy to use
from strategy.rolling_return import RollingReturnStrategy

STRATEGY_CLASS = RollingReturnStrategy
STRATEGY_PARAMS = {
    "window": 5,
    "long_th": 0.1,
    "short_th": -0.1,
}

# Candle resolution and order throttling
RESOLUTION = "1m"  # 1m, 5m, 1h, 1d, etc.
THROTTLE = 0.5     # Min seconds between orders

# Logging
LOG_LEVEL = "INFO"
LOG_TO_FILE = True
LOG_TO_CONSOLE = True
```

### Switching Brokers

```python
# For paper trading (simulation)
BROKER_TYPE = "paper"
PAPER_BROKER_CONFIG = {"initial_balance": 50000.0}

# For live trading with real money
BROKER_TYPE = "live"
```

### Switching Strategies

Change the strategy and its parameters:

```python
# Option 1: Rolling Return Strategy
from strategy.rolling_return import RollingReturnStrategy

STRATEGY_CLASS = RollingReturnStrategy
STRATEGY_PARAMS = {
    "window": 5,
    "long_th": 0.1,
    "short_th": -0.1,
}

# Option 2: Max Breakout Short Strategy
from strategy.max_breakout_short_strategy import MaxBreakoutShortStrategy

STRATEGY_CLASS = MaxBreakoutShortStrategy
STRATEGY_PARAMS = {
    "lookback_period": 180,
    "stop_loss_pct": 1.0,
    "target_return_pct": 3.0,
}
```

## How It Works

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    main.py (Entry Point)                     │
│              Reads all config from trading_config.py          │
└────────────────┬────────────────────────────────────────────┘
                 │
     ┌───────────┴────────────┬────────────────┐
     │                        │                │
     ▼                        ▼                ▼
┌─────────────┐       ┌──────────────┐   ┌──────────────┐
│  Broker     │       │  Strategy    │   │  WebSocket   │
│  (Paper/    │       │  (Rolling    │   │  Market Data │
│   Live)     │       │   Return,    │   │  Streamer    │
└────┬────────┘       │   Max        │   └──────┬───────┘
     │                │   Breakout)  │          │
     │                └──────┬───────┘          │
     │                       │                  │
     └───────────────────────┴──────────────────┘
              ▼
     ┌──────────────────┐
     │  Engine Runner   │
     │  (Coordinates)   │
     └──────────────────┘
```

### Execution Flow

1. **Startup** (`main.py`):
   - Loads configuration from `config/trading_config.py`
   - Creates broker instance (Paper or Live)
   - Creates strategy instances (one per symbol)
   - Sets up logging and signal handlers

2. **Data Stream** (`data/websocket.py`):
   - Connects to WebSocket market data feed
   - Streams candlesticks in real-time
   - Passes candles to the engine

3. **Strategy Update** (`engine/runner.py`):
   - Each strategy processes the new candle
   - Generates signal: 1 (long), -1 (short), or 0 (flat)
   - Compares with last signal to detect changes

4. **Order Execution** (`execution/broker.py`):
   - If signal changed, submit order to broker
   - Paper broker simulates fills; Live broker submits to exchange
   - Tracks position, P&L, and trade statistics

5. **Monitoring & Logging**:
   - Real-time logging of trades, P&L, and errors
   - Timestamped log files in `logs/` directory

## Usage

### Running the Bot

**Paper Trading (Safe for Testing)**:
```bash
uv run main.py
```

**With Specific Resolution**:
Edit `RESOLUTION` in `config/trading_config.py`, then run:
```bash
uv run main.py
```

**View Logs**:
```bash
tail -f logs/trading_bot_*.log
```

### Example Workflows

#### Example 1: Paper Trade with Rolling Return Strategy

1. Edit `config/trading_config.py`:
```python
BROKER_TYPE = "paper"
STRATEGY_CLASS = RollingReturnStrategy
STRATEGY_PARAMS = {"window": 5, "long_th": 0.1, "short_th": -0.1}
```

2. Run:
```bash
uv run main.py
```

3. Monitor trades in `logs/trading_bot_*.log`

#### Example 2: Test Max Breakout Strategy

1. Edit `config/trading_config.py`:
```python
BROKER_TYPE = "paper"
STRATEGY_CLASS = MaxBreakoutShortStrategy
STRATEGY_PARAMS = {
    "lookback_period": 180,
    "stop_loss_pct": 1.0,
    "target_return_pct": 3.0,
}
PAPER_BROKER_CONFIG = {"initial_balance": 50000.0}
```

2. Run and observe P&L tracking

#### Example 3: Trade Multiple Symbols

1. Set environment variable or `config/settings.py`:
```python
SYMBOLS = ["BTCUSD", "ETHUSD", "SOLUSD"]
```

2. Run `main.py` - strategies run independently per symbol

## Strategies

### Rolling Return Strategy

**File**: `strategy/rolling_return.py`

**How It Works**:
- Calculates percentage return over a rolling window
- Generates LONG signal when average return exceeds `long_th`
- Generates SHORT signal when average return falls below `short_th`
- FLAT signal when return is between thresholds

**Parameters**:
- `window`: Number of candles to look back (default: 5)
- `long_th`: Threshold for long signal in % (default: 0.1)
- `short_th`: Threshold for short signal in % (default: -0.1)

**Usage**:
```python
STRATEGY_CLASS = RollingReturnStrategy
STRATEGY_PARAMS = {
    "window": 5,
    "long_th": 0.1,
    "short_th": -0.1,
}
```

### Max Breakout Short Strategy

**File**: `strategy/max_breakout_short_strategy.py`

**How It Works**:
- Tracks rolling maximum close price over lookback period
- Takes SHORT position when current close exceeds the rolling max
- Automatically exits when:
  - Stop loss hit (loss >= configured %)
  - Target return achieved (profit >= configured %)
- Tracks P&L and win rate

**Parameters**:
- `lookback_period`: Candles to look back for max (default: 180)
- `stop_loss_pct`: Stop loss percentage (default: 1.0)
- `target_return_pct`: Target profit percentage (default: 3.0)

**Usage**:
```python
STRATEGY_CLASS = MaxBreakoutShortStrategy
STRATEGY_PARAMS = {
    "lookback_period": 180,
    "stop_loss_pct": 1.0,
    "target_return_pct": 3.0,
}
```

### Creating Custom Strategies

1. Create a new file in `strategy/` directory:

```python
# strategy/my_strategy.py

class MyStrategy:
    def __init__(self, param1: int = 10, param2: float = 0.5):
        self.param1 = param1
        self.param2 = param2
        self.last_signal = 0  # REQUIRED
        
    def update(self, candle: dict) -> int:
        """
        Process new candle and return signal.
        
        Args:
            candle: {
                "close": float,
                "open": float,
                "high": float,
                "low": float,
                "volume": float,
                "symbol": str,
                "resolution": str,
                "timestamp": int
            }
            
        Returns:
            1 for long, -1 for short, 0 for flat
        """
        close = candle["close"]
        
        # Your logic here
        if close > 100:
            self.last_signal = 1
        elif close < 50:
            self.last_signal = -1
        else:
            self.last_signal = 0
            
        return self.last_signal
```

2. Update `config/trading_config.py`:

```python
from strategy.my_strategy import MyStrategy

STRATEGY_CLASS = MyStrategy
STRATEGY_PARAMS = {
    "param1": 20,
    "param2": 0.75,
}
```

3. Run:

```bash
uv run main.py
```

## Project Structure

```
bot/
├── main.py                          # Main entry point (DO NOT EDIT)
├── pyproject.toml                   # Project metadata and dependencies
├── README.md                        # This file
├── CONFIG_GUIDE.md                  # Detailed configuration guide
│
├── config/
│   ├── settings.py                  # API credentials and symbols
│   └── trading_config.py            # Strategy and broker configuration
│
├── data/
│   ├── websocket.py                 # WebSocket market data streaming
│   └── parser.py                    # Candlestick data parsing
│
├── execution/
│   ├── broker.py                    # Live broker API client
│   ├── paper_broker.py              # Paper trading simulator
│   └── signer.py                    # API request signing
│
├── engine/
│   └── runner.py                    # Trading engine (strategy & order coordination)
│
├── strategy/
│   ├── template_strategy.py         # Template for creating strategies
│   ├── rolling_return.py            # Rolling return strategy
│   ├── max_breakout_short_strategy.py # Breakout short strategy
│   └── example_strategy.py          # Example SMA strategy
│
├── utils/
│   └── logger.py                    # Logging configuration
│
├── mains_custom/                    # Alternative main scripts
│   ├── main_paper.py                # Paper trading (generic)
│   ├── main_paper_max_breakout.py   # Paper trading with max breakout
│   ├── main_live_max_breakout.py    # Live trading with max breakout
│   ├── main_multi_strategy.py       # Multiple strategies
│   ├── backtest.py                  # Backtesting framework
│   └── template_main.py             # Template for custom mains
│
└── logs/                            # Generated log files (timestamped)
```

## Advanced Usage

### Running Alternative Main Scripts

The `mains_custom/` folder contains specialized entry points:

```bash
# Paper trading with max breakout strategy
uv run mains_custom/main_paper_max_breakout.py

# Live trading (requires real credentials)
uv run mains_custom/main_live_max_breakout.py

# Multi-symbol with multiple strategies
uv run mains_custom/main_multi_strategy.py

# Backtest strategy on historical data
uv run mains_custom/backtest.py
```

### Accessing Broker Statistics

```python
# After trades, check statistics:
broker.stats  # Per-symbol statistics
broker.balance  # Current account balance
broker.positions  # Current open positions
broker.trade_history  # List of all trades
```

### Setting Different Resolutions

```python
# 1-minute candles (fastest signals)
RESOLUTION = "1m"

# 5-minute candles (balanced)
RESOLUTION = "5m"

# 1-hour candles (fewer trades, higher conviction)
RESOLUTION = "1h"

# Daily candles (trend following)
RESOLUTION = "1d"
```

### Custom Logging

Override in `config/trading_config.py`:

```python
LOG_LEVEL = "DEBUG"    # More verbose
LOG_TO_FILE = True     # Save to logs/
LOG_TO_CONSOLE = True  # Print to terminal
```

View logs:
```bash
tail -f logs/trading_bot_*.log
```

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'websockets'"

**Solution**: Install dependencies:
```bash
uv sync
# or
pip install websockets aiohttp pandas
```

### Issue: "KeyError: 'close' when parsing candle"

**Solution**: Ensure WebSocket data format includes required fields. Check `data/parser.py` for expected candlestick structure.

### Issue: Strategy not trading (no signals)

**Debug Steps**:
1. Set `LOG_LEVEL = "DEBUG"` in config
2. Check log files for candle data being received
3. Verify strategy parameters make sense for current market
4. Test with `PAPER_BROKER_CONFIG` first before live trading

### Issue: Paper broker shows no balance after trading

**Solution**: Check `broker.stats` dictionary for per-symbol P&L. Balance is reduced when losses occur.

### Issue: Connection timeout to WebSocket

**Solution**:
1. Verify `WS_URL` in `config/settings.py` is correct
2. Check internet connectivity
3. Try setting different symbols in `SYMBOLS`
4. Enable DEBUG logging to see connection errors

### Issue: "API key invalid" on live trading

**Solution**:
1. Verify credentials in environment variables:
   ```bash
   echo $DELTA_API_KEY
   echo $DELTA_API_SECRET
   ```
2. Ensure credentials have trading permissions
3. Check credentials are for correct API endpoint
4. Test with paper broker first

## Performance Tips

1. **Use appropriate resolution**: Higher resolution (5m, 1h) = fewer updates = lower CPU usage
2. **Set reasonable `THROTTLE`**: Prevents order spam. Minimum 0.5 seconds recommended.
3. **Monitor logs**: Keeps system responsive. Log to file only if file I/O is fast
4. **Test with paper broker first**: Before risking real money, validate strategy with `BROKER_TYPE = "paper"`
5. **Use appropriate `lookback_period`**: Longer lookbacks use more memory; balance with strategy accuracy

## License

This project is proprietary. Do not distribute without permission.

## Support

For issues, check the logs in `logs/` directory and review the relevant source files referenced in error messages.