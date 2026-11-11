from django.core.management.base import BaseCommand
from apps.market_data.models import Stock


STOCKS = [
    {
        "symbol": "RELIANCE",
        "company_name": "Reliance Industries Limited",
        "exchange": "NSE",
        "sector": "Energy",
    },
    {
        "symbol": "TCS",
        "company_name": "Tata Consultancy Services",
        "exchange": "NSE",
        "sector": "Information Technology",
    },
    {
        "symbol": "INFY",
        "company_name": "Infosys Limited",
        "exchange": "NSE",
        "sector": "Information Technology",
    },
    {
        "symbol": "HDFCBANK",
        "company_name": "HDFC Bank Limited",
        "exchange": "NSE",
        "sector": "Banking",
    },
    {
        "symbol": "ICICIBANK",
        "company_name": "ICICI Bank Limited",
        "exchange": "NSE",
        "sector": "Banking",
    },
    {
        "symbol": "SBIN",
        "company_name": "State Bank of India",
        "exchange": "NSE",
        "sector": "Banking",
    },
    {
        "symbol": "ITC",
        "company_name": "ITC Limited",
        "exchange": "NSE",
        "sector": "FMCG",
    },
    {
        "symbol": "WIPRO",
        "company_name": "Wipro Limited",
        "exchange": "NSE",
        "sector": "Information Technology",
    },
    {
        "symbol": "LT",
        "company_name": "Larsen & Toubro Limited",
        "exchange": "NSE",
        "sector": "Infrastructure",
    },
    {
        "symbol": "BHARTIARTL",
        "company_name": "Bharti Airtel Limited",
        "exchange": "NSE",
        "sector": "Telecommunications",
    },
]


class Command(BaseCommand):
    help = "Seed initial NSE stocks into the database"

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

        for stock_data in STOCKS:
            _, created = Stock.objects.update_or_create(
                symbol=stock_data["symbol"],
                exchange=stock_data["exchange"],
                defaults=stock_data,
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Stock seeding completed. "
                f"Created: {created_count}, Updated: {updated_count}"
            )
        )