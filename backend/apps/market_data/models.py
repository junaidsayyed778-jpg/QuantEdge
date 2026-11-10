from django.db import models


class Stock(models.Model):
    symbol = models.CharField(max_length=10, unique=True)
    company_name = models.CharField(max_length=255)
    exchange = models.CharField(max_length=10)
    sector = models.CharField(max_length=100, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "stocks"
        constraints = [
            models.UniqueConstraint(fields=["symbol"], name="unique_stock_symbol"),
            models.UniqueConstraint(
                fields=["symbol", "exchange"], name="unique_stock_exchange"
            ),
        ]
        ordering = ["symbol"]

    def __str__(self):
        return f"{self.symbol} - {self.exchange}"


class HistoricalPrice(models.Model):
    stock = models.ForeignKey(
        Stock,
        on_delete=models.CASCADE,
        related_name="historical_prices",
    )
    trading_date = models.DateField()

    open = models.DecimalField(max_digits=10, decimal_places=2)
    high = models.DecimalField(max_digits=10, decimal_places=2)
    low = models.DecimalField(max_digits=10, decimal_places=2)
    close = models.DecimalField(max_digits=10, decimal_places=2)
    adjusted_close = models.DecimalField(max_digits=10, decimal_places=2)
    volume = models.BigIntegerField()

    data_source = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "historical_prices"
        constraints = [
            models.UniqueConstraint(
                fields=["stock", "trading_date"],
                name="unique_stock_trading_data",
            ),
        ]
        indexes = [
            models.Index(fields=["stock", "trading_date"], name="trading_date_idx"),
        ]
        ordering = ["-trading_date"]

    def __str__(self):
        return f"{self.stock.symbol} - {self.trading_date}"