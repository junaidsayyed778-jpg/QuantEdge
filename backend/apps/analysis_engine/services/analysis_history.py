from datetime import date
from decimal import Decimal

from apps.market_data.models import Stock
from apps.analysis_engine.models import StockAnalysis

def save_analysis(user, result):
    
    stock = Stock.objects.get(
        symbol=result["stock"]["symbol"]
    )
    
    analysis_date = date.fromisoformat(
        result["analysis_date"]
    )
    
    analysis, created = StockAnalysis.objects.update_or_create(
        user=user,
        stock=stock,
        analysis_date=analysis_date,
    
    
    defaults={
        "latest_close": Decimal(
            str(result["latest_close"])
        ),
        
        "overall_score": result["scores"]["overall_score"],
        "signal": result["scores"]["signal"],
        "category_scores": result["scores"]["category_scores"],
        "support_zones": result["support_zones"],
        "resistance_zones": result["resistance_zones"],
    },
    
    )
    return analysis, created
    