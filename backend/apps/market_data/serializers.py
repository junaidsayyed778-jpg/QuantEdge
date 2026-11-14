from rest_framework import serializers
from .models import Stock

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
    
    class Meta:
        model = Stock
        fields = [
            "id",
            "stock",
            "trading_date",
            "open",
            "high",
            "low",
            "close",
            "adjusted_close",
            "volume",
            "data_source",
            "created_at",
        ]
        
        read_only_fields = ["id", "created_at"]