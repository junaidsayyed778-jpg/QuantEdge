from django.core.management.base import BaseCommand, CommandError

from apps.market_data.services.stock_sync import StockSyncService


class Command(BaseCommand):
    help = "Synchronize NSE stock instruments from Twelve Data."

    def handle(self, *args, **options):
        try:
            result = StockSyncService().sync_stocks()

        except Exception as error:
            raise CommandError(
                f"Stock synchronization failed: {error}"
            ) from error

        self.stdout.write(
            self.style.SUCCESS(
                f"Stock sync completed!\n"
                f"Total received: {result['total_received']}\n"
                f"Valid common stocks: {result['valid_stocks']}\n"
                f"Upserted: {result['synced']}"
            )
        )