from django.core.management.base import BaseCommand, CommandError

from apps.market_data.models import Stock
from apps.market_data.services.historical_price import (
    HistoricalPriceService,
)


class Command(BaseCommand):

    help = "Synchronize historical stock prices from Yahoo Finance."

    def add_arguments(self, parser):
        parser.add_argument(
            "--symbol",
            type=str,
            required=True,
            help="Stock symbol, e.g. RELIANCE",
        )

        parser.add_argument(
            "--period",
            type=str,
            default="1mo",
            help="Historical period, e.g. 1mo, 3mo, 6mo, 1y",
        )

        parser.add_argument(
            "--interval",
            type=str,
            default="1d",
            help="Data interval, e.g. 1d, 1wk, 1mo",
        )

    def handle(self, *args, **options):

        symbol = options["symbol"].strip().upper()
        period = options["period"]
        interval = options["interval"]

        if not Stock.objects.filter(
            symbol=symbol,
            exchange="NSE",
            is_active=True,
        ).exists():
            raise CommandError(
                f"Active NSE stock '{symbol}' was not found."
            )

        try:
            result = HistoricalPriceService().sync_stock_history(
                symbol=symbol,
                period=period,
                interval=interval,
            )

        except Exception as error:
            raise CommandError(
                f"Historical price synchronization failed: {error}"
            ) from error

        self.stdout.write(
            self.style.SUCCESS(
                f"Historical synchronization completed!\n"
                f"Symbol: {result['symbol']}\n"
                f"Records received: {result['records_received']}\n"
                f"Records synced: {result['records_synced']}"
            )
        )