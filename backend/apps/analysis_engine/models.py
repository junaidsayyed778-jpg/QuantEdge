from django.db import models
from django.conf import settings


class StockAnalysis(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="stock_analyses",
    )

    stock = models.ForeignKey(
        "market_data.stock",
        on_delete=models.CASCADE,
        related_name="analyses",
    )

    analysis_date = models.DateField()

    latest_close = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    overall_score = models.FloatField()

    signal = models.CharField(
        max_length=30,
    )

    category_scores = models.JSONField(default=dict)

    support_zones = models.JSONField(default=list)


    resistance_zones = models.JSONField(default=list)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "stock_analyses"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.stock.symbol} - {self.analysis_date}"