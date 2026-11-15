from rest_framework import serializers
from .models import Stock, HistoricalPrice


class StockSerializer(serializers.ModelSerializer):

    class Meta:
        model = Stock
        fields = [
            "id",
            "symbol",
            "company_name",
            "exchange",
            "sector",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class HistoricalPriceSerializer(serializers.ModelSerializer):

    date = serializers.DateField(source="trading_date")

    class Meta:
        model = HistoricalPrice
        fields = [
            "date",
            "open",
            "high",
            "low",
            "close",
            "adjusted_close",
            "volume",
            "data_source",
        ]