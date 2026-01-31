def parse_candlestick(msg: dict) -> dict | None:
    """
    Parses Delta Exchange candlestick messages and converts to proper types.

    Expected (example):
    {
        "type": "candlestick_1m",
        "candle_start_time": 1596015240000000,
        "close": "9223",
        "high": "9228",
        "low": "9220",
        "open": "9221",
        "resolution": "1m",
        "symbol": "BTCUSD",
        "timestamp": 1596015289339699,
        "volume": "1.2"
    }
    
    Returns full dictionary with all fields converted to appropriate types.
    """

    # Required fields
    if "close" not in msg:
        return None

    try:
        # Convert numeric fields
        parsed = {
            "close": float(msg["close"]),
            "open": float(msg.get("open", msg["close"])),
            "high": float(msg.get("high", msg["close"])),
            "low": float(msg.get("low", msg["close"])),
        }

        # Optional numeric fields
        if "volume" in msg:
            parsed["volume"] = float(msg["volume"])

        # String fields
        if "symbol" in msg:
            parsed["symbol"] = str(msg["symbol"])
        if "resolution" in msg:
            parsed["resolution"] = str(msg["resolution"])
        if "type" in msg:
            parsed["type"] = str(msg["type"])

        # Timestamp fields (keep as int, could be very large)
        if "timestamp" in msg:
            parsed["timestamp"] = int(msg["timestamp"])
        if "candle_start_time" in msg:
            parsed["candle_start_time"] = int(msg["candle_start_time"])

        return parsed

    except (ValueError, TypeError):
        return None
