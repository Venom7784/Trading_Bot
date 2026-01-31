import json
import websockets
from .parser import parse_candlestick

# Supported resolutions
SUPPORTED_RESOLUTIONS = ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "12h", "1d", "1w"]


async def candlestick_stream(
    ws_url: str,
    symbols: list[str] | str,
    resolutions: list[str] | None = None,
):
    """
    Async generator yielding parsed candlesticks for specified resolutions and symbols.
    
    Args:
        ws_url: WebSocket URL
        symbols: Trading symbol(s) - can be a single string or list of strings (e.g., "BTCUSD" or ["BTCUSD", "ETHUSD"])
        resolutions: List of resolutions to subscribe to (e.g., ["1m", "5m"])
                    If None, defaults to ["1m"]
    
    Yields:
        Dictionary with parsed candlestick data including all fields
    """
    # Normalize symbols to list
    if isinstance(symbols, str):
        symbols = [symbols]
    
    if resolutions is None:
        resolutions = ["1m"]
    
    # Validate resolutions
    invalid = [r for r in resolutions if r not in SUPPORTED_RESOLUTIONS]
    if invalid:
        raise ValueError(f"Unsupported resolutions: {invalid}. Supported: {SUPPORTED_RESOLUTIONS}")
    
    # Build subscription message - group all symbols by resolution
    channels = [
        {
            "name": f"candlestick_{res}",
            "symbols": symbols
        }
        for res in resolutions
    ]
    
    subscribe_msg = {
        "type": "subscribe",
        "payload": {
            "channels": channels
        }
    }

    async with websockets.connect(
        ws_url,
        ping_interval=10,
        ping_timeout=5,
        max_size=None
    ) as ws:
        await ws.send(json.dumps(subscribe_msg))
        print(f"[WS] Subscribed to {len(symbols)} symbol(s) on resolutions: {resolutions}")
        if len(symbols) <= 10:
            print(f"[WS] Symbols: {', '.join(symbols)}")
        else:
            print(f"[WS] First 10 symbols: {', '.join(symbols[:10])}...")

        # Track last processed candle_start_time per symbol to avoid duplicate processing
        # Delta sends multiple updates per candle as it progresses, but we only want to process each candle once
        last_candle_ts: dict[str, int] = {}

        async for raw in ws:
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8", errors="ignore")

            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            # Handle subscription confirmation
            if msg.get("type") == "subscriptions":
                continue

            # Check if this is a candlestick message by looking for candlestick fields
            # Messages can have "type": "candlestick_1m" OR have fields like "candle_start_time", "close", etc.
            is_candlestick = (
                msg.get("type", "").startswith("candlestick") or
                ("candle_start_time" in msg or "close" in msg) and "symbol" in msg and "resolution" in msg
            )
            
            if not is_candlestick:
                continue

            # Get candle_start_time to check if this is a new candle or an update to the current one
            candle_start_time = msg.get("candle_start_time")
            symbol = msg.get("symbol")
            
            if candle_start_time is None or symbol is None:
                continue
            
            # Skip if this is an update to the same candle we already processed
            if symbol in last_candle_ts and candle_start_time == last_candle_ts[symbol]:
                continue
            
            # This is a new candle, update tracking and process it
            last_candle_ts[symbol] = candle_start_time

            parsed = parse_candlestick(msg)
            if parsed:
                yield parsed