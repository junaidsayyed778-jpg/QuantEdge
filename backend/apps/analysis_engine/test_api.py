from rest_framework import status
from rest_framework.test import APITestCase

from apps.market_data.models import Stock, HistoricalPrice
from django.contrib.auth import get_user_model

from unittest.mock import patch


User = get_user_model()


class StockAnalysisAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="TestPassword123!",
        )

        self.stock = Stock.objects.create(
            symbol="TEST",
            company_name="Test Company",
            exchange="NSE",
            is_active=True,
        )

        self.url = "/api/v1/analysis/stocks/TEST/"

    def test_unauthenticated_request(self):
        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    @patch("apps.analysis_engine.views.analyze_stock")
    def test_successful_analysis(self, mock_analyze):
        mock_analyze.return_value = {
            "stock": {
                "symbol": "TEST",
                "company_name": "Test Company",
                "exchange": "NSE",
            },
            "analysis_date": "2026-11-21",
            "latest_close": 150.0,
            "scores": {
                "overall_score": 65,
                "signal": "strong_bullish",
                "category_scores": {},
            },
            "support_zones": [],
            "resistance_zones": [],
        }

        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["stock"]["symbol"], "TEST")
        self.assertEqual(response.data["latest_close"], 150.0)

    @patch("apps.analysis_engine.views.analyze_stock")
    def test_invalid_stock(self, mock_analyze):
        mock_analyze.side_effect = ValueError("Stock not found.")

        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            "/api/v1/analysis/stocks/INVALID/"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error", response.data)

    @patch("apps.analysis_engine.views.analyze_stock")
    def test_insufficient_historical_data(self, mock_analyze):
        mock_analyze.side_effect = ValueError(
            "At least 200 historical records are required."
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error", response.data)