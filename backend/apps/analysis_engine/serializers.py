from rest_framework import serializers

from .models import StockAnalysis


class AnalysisHistorySerializer(serializers.ModelSerializer):
    stock_symbol = serializers.CharField(source="stock.symbol")
    company_name = serializers.CharField(source="stock.company_name")
    exchange = serializers.CharField(source="stock.exchange")

    class Meta:
        model = StockAnalysis
        fields = [
            "id",
            "stock_symbol",
            "company_name",
            "exchange",
            "analysis_date",
            "latest_close",
            "overall_score",
            "signal",
            "category_scores",
            "created_at",
        ]