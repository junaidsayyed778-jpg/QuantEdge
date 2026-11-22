from rest_framework import status
from rest_framework.test import APITestCase

from apps.analysis_engine.models import StockAnalysis
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

        self.assertEqual(
            StockAnalysis.objects.filter(user=self.user).count(),
            1,
        )
        self.assertTrue(response.data["history"]["created"])

        second_response = self.client.get(self.url)

        self.assertEqual(
            second_response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            StockAnalysis.objects.filter(user=self.user).count(),
            1,
        )
        self.assertFalse(second_response.data["history"]["created"])

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
        
class AnalysisHistoryAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="historyuser",
            email="history@example.com",
            password="TestPassword123!",
        )

        self.other_user = User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="TestPassword123!",
        )

        self.stock = Stock.objects.create(
            symbol="HIST",
            company_name="History Company",
            exchange="NSE",
            is_active=True,
        )

        self.url = "/api/v1/analysis/history/"

    def create_analysis(self, user, analysis_date, score=50):
        return StockAnalysis.objects.create(
            user=user,
            stock=self.stock,
            analysis_date=analysis_date,
            latest_close=150.00,
            overall_score=score,
            signal="bullish",
            category_scores={"trend": 75},
            support_zones=[],
            resistance_zones=[],
        )

    def test_unauthenticated_history_request(self):
        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_user_can_only_see_own_history(self):
        self.create_analysis(self.user, "2026-11-20")
        self.create_analysis(self.other_user, "2026-11-21")

        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["stock_symbol"],
            "HIST",
        )

    def test_empty_history(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(response.data["results"], [])

    def test_history_pagination(self):
        for day in range(1, 13):
            self.create_analysis(
                self.user,
                f"2026-10-{day:02d}",
            )

        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            self.url,
            {"page": 1, "page_size": 5},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 12)
        self.assertEqual(len(response.data["results"]), 5)
        self.assertIsNotNone(response.data["next"])