from django.db import transaction

from apps.market_data.models import Stock
from apps.market_data.services.twelve_data import TwelveDataClient

class StockSyncService:
    
    def __init__(self):
        self.client = TwelveDataClient()
        
    def sync_stocks(self):
        response = self.client.get_stocks(
                    country = "India",
                    exchange = "NSE"
        )
        
        instruments = response.get("data", [])
        
        if not instruments:
            raise ValueError("No stock data found in the response.")    
        
        stocks = {}
        
        for instrument in instruments:
            
            if instrument.get("type") != "Common Stock":
                continue
            
            symbol = instrument.get("symbol")
            company_name = instrument.get("name")
            exchange = instrument.get("exchange")
            
            if not symbol or not company_name or not exchange:
                continue
            
            key = (symbol, exchange)
            
            stocks[key] = Stock(
                symbol=symbol,
                company_name=company_name,
                exchange=exchange,
                is_active=True,
            )

        stock_objects = list(stocks.values())
        
        if not stock_objects:
            raise ValueError("No valid stock data to sync.")
        
        with transaction.atomic():
            Stock.objects.bulk_create(
                stock_objects,
                batch_size=100,
                update_conflicts=True,
                unique_fields=["symbol", "exchange"],
                update_fields=["company_name", "is_active"]
            )
            
        return {
            "total_received": len(instruments),
            "valid_stocks": len(stock_objects),
            "synced": len(stock_objects),
        }