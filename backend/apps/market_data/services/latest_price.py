from apps.market_data.models import Stock
from apps.market_data.services.yahoo_finance import YahooFinanceClient


class LatestPriceService:

    def __init__(self):
        self.client = YahooFinanceClient()

    def get_stock_latest_price(self, symbol):

        stock = Stock.objects.get(
            symbol=symbol.upper(),
            exchange="NSE",
            is_active=True,
        )

        yahoo_symbol = f"{stock.symbol}.NS"

        latest_data = self.client.get_latest_price(yahoo_symbol)

        return {
            "symbol": stock.symbol,
            "company_name": stock.company_name,
            **latest_data,
            "data_source": "Yahoo Finance",
        }