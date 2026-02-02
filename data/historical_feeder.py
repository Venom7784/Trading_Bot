import asyncio
from datetime import datetime, timedelta
from data.historical_collector import HistoricalDataCollector, get_unix_timestamp


import aiohttp

async def feed_historical_data_to_strategy(strategy, symbol, days_back, resolutions, session=None):
    """
    Fetch historical data and feed it to the strategy without trading.
    Returns the strategy after being updated with historical candles.
    """
    end = get_unix_timestamp(datetime.utcnow())
    start = get_unix_timestamp(datetime.utcnow() - timedelta(days=days_back))
    close_session = False
    if session is None:
        session = aiohttp.ClientSession()
        close_session = True
    collector = HistoricalDataCollector(symbol, start, end, resolutions, session)
    all_data = await collector.collect_all()

    # Feed each candle to the strategy (no trading)
    for res, candles in all_data.items():
        # Expecting candles['result'] to be a list of dicts with OHLCV
        for candle in candles.get('result', []):
            # Skip dummy candles (all zero values)
            if (
                float(candle.get('open', 0)) == 0 and
                float(candle.get('high', 0)) == 0 and
                float(candle.get('low', 0)) == 0 and
                float(candle.get('close', 0)) == 0 and
                float(candle.get('volume', 0)) == 0
            ):
                continue
            candle_dict = {
                'open': float(candle['open']),
                'high': float(candle['high']),
                'low': float(candle['low']),
                'close': float(candle['close']),
                'volume': float(candle.get('volume', 0)),
                'timestamp': int(candle.get('time', 0)),
                'resolution': res,
                'symbol': symbol,
            }
            # Feed to strategy, but ignore the signal
            strategy.update(candle_dict)
    if close_session:
        await session.close()
    return strategy

# Example usage:
# from data.historical_feeder import feed_historical_data_to_strategy
# strategy = YourStrategy(...)
# asyncio.run(feed_historical_data_to_strategy(strategy, 'BTCUSD', 30, ['5m']))
