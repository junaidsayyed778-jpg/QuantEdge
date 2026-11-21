import math
from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase

from apps.market_data.models import Stock, HistoricalPrice
from apps.analysis_engine.services.stock_analysis import analyze_stock


class StockAnalysisIntegrationTests(TestCase):

    def setUp(self):
        self.stock = Stock.objects.create(
            symbol="TEST",
            company_name="Test Company",
            exchange="NSE",
            is_active=True,
        )

        historical_records = []

        for i in range(250):
            close = 100 + (i * 0.15) + (math.sin(i / 5) * 4)
            open_price = close + (math.sin(i / 3) * 0.6)

            high = max(open_price, close) + 1.5
            low = min(open_price, close) - 1.5

            historical_records.append(
                HistoricalPrice(
                    stock=self.stock,
                    trading_date=date(2025, 1, 1) + timedelta(days=i),
                    open=Decimal(str(round(open_price, 2))),
                    high=Decimal(str(round(high, 2))),
                    low=Decimal(str(round(low, 2))),
                    close=Decimal(str(round(close, 2))),
                    adjusted_close=Decimal(str(round(close, 2))),
                    volume=100000 + (i % 20) * 5000,
                    data_source="TEST",
                )
            )

        HistoricalPrice.objects.bulk_create(historical_records)

    def test_successful_stock_analysis(self):
        result = analyze_stock("TEST")

        self.assertEqual(result["stock"]["symbol"], "TEST")
        self.assertIn("analysis_date", result)
        self.assertGreater(result["current_price"], 0)

        self.assertIn("overall_score", result["scores"])
        self.assertIn("signal", result["scores"])
        self.assertIn("category_scores", result["scores"])

        self.assertIsInstance(result["support_zones"], list)
        self.assertIsInstance(result["resistance_zones"], list)

    def test_invalid_stock(self):
        with self.assertRaises(ValueError):
            analyze_stock("INVALID")

    def test_inactive_stock(self):
        self.stock.is_active = False
        self.stock.save()

        with self.assertRaises(ValueError):
            analyze_stock("TEST")

    def test_insufficient_historical_records(self):
        HistoricalPrice.objects.filter(stock=self.stock).delete()

        with self.assertRaises(ValueError):
            analyze_stock("TEST")