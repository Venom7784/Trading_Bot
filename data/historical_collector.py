
import aiohttp
from datetime import datetime, timedelta


class HistoricalDataCollector:
    def __init__(self, symbol, start_time, end_time, resolutions, session: aiohttp.ClientSession):
        self.symbol = symbol
        self.start_time = start_time  # Unix timestamp
        self.end_time = end_time      # Unix timestamp
        self.resolutions = resolutions if isinstance(resolutions, list) else [resolutions]
        self.base_url = 'https://api.india.delta.exchange/v2/history/candles'
        self.headers = {'Accept': 'application/json'}
        self.session = session

    async def fetch_candles(self, resolution):
        params = {
            'resolution': resolution,
            'symbol': self.symbol,
            'start': str(self.start_time),
            'end': str(self.end_time)
        }
        async with self.session.get(self.base_url, params=params, headers=self.headers) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def collect_all(self):
        data = {}
        for res in self.resolutions:
            data[res] = await self.fetch_candles(res)
        return data


def get_unix_timestamp(dt):
    return int(dt.timestamp())

# Example usage:
# from data.historical_collector import HistoricalDataCollector, get_unix_timestamp
# start = get_unix_timestamp(datetime.utcnow() - timedelta(days=30))
# end = get_unix_timestamp(datetime.utcnow())
# collector = HistoricalDataCollector('BTCUSD', start, end, ['5m', '1h'])
# candles = collector.collect_all()
