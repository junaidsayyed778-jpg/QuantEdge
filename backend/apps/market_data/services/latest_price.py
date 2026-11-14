from django.core.cache import cache
from apps.market_data.models import Stock
from apps.market_data.services.yahoo_finance import YahooFinanceClient


class LatestPriceService:
    CACHE_TIMEOUT = 60

    def __init__(self):
        self.client = YahooFinanceClient()

    def get_stock_latest_price(self, symbol):
        symbol = symbol.upper()

        # check redis cache
        cache_key = f"latest_stock_price:{symbol}"
        cached_data = cache.get(cache_key)

        if cached_data is not None:
            print(f"REDIS CACHE HIT: {symbol}: {cached_data}")
            return cached_data

        print(f"REDIS CACHE MISS: {symbol}")

        # Fetch stock from database
        stock = Stock.objects.get(
            symbol=symbol,
            exchange="NSE",
            is_active=True,
        )

        # Fetch latest price from yahoo Finance
        yahoo_symbol = f"{stock.symbol}.NS"
        latest_price = self.client.get_latest_price(yahoo_symbol)

        result = {
            "symbol": stock.symbol,
            "exchange": stock.exchange,
            "latest_price": latest_price,
        }

        # Store in cache
        cache.set(cache_key, result, self.CACHE_TIMEOUT)

        return result