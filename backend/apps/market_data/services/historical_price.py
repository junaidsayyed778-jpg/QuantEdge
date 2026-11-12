#Fetch and store historical OHLCV

from decimal import Decimal

from django.db import transaction

from apps.market_data.models import Stock, HistoricalPrice
from apps.market_data.services.yahoo_finance import YahooFinanceClient


class HistoricalPriceService:

    def __init__(self):
        self.client = YahooFinanceClient()

    @transaction.atomic
    def sync_stock_history(
        self,
        symbol,
        period="1mo",
        interval="1d",
    ):
        # Find the stock in our database.
        stock = Stock.objects.get(
            symbol=symbol,
            exchange="NSE",
        )

        # Yahoo Finance uses .NS for NSE stocks.
        yahoo_symbol = f"{symbol}.NS"

        data = self.client.get_time_series(
            symbol=yahoo_symbol,
            period=period,
            interval=interval,
        )

        price_objects = []

        for timestamp, row in data.iterrows():

            price_objects.append(
                HistoricalPrice(
                    stock=stock,
                    trading_date=timestamp.date(),
                    open=Decimal(str(row["Open"])),
                    high=Decimal(str(row["High"])),
                    low=Decimal(str(row["Low"])),
                    close=Decimal(str(row["Close"])),
                    adjusted_close=Decimal(
                        str(row["Adj Close"])
                    ) if "Adj Close" in data.columns else None,
                    volume=int(row["Volume"]),
                    data_source="Yahoo Finance",
                )
            )

        if not price_objects:
            raise ValueError(
                f"No historical prices found for {symbol}."
            )

        # Insert new records and update existing records.
        HistoricalPrice.objects.bulk_create(
            price_objects,
            batch_size=500,
            update_conflicts=True,
            unique_fields=["stock", "trading_date"],
            update_fields=[
                "open",
                "high",
                "low",
                "close",
                "adjusted_close",
                "volume",
                "data_source",
            ],
        )

        return {
            "symbol": symbol,
            "records_received": len(data),
            "records_synced": len(price_objects),
        }