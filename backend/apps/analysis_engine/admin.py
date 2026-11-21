from django.contrib import admin
from .models import StockAnalysis


@admin.register(StockAnalysis)
class StockAnalysisAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "stock",
        "analysis_date",
        "latest_close",
        "overall_score",
        "signal",
        "created_at",
    )

    list_filter = (
        "signal",
        "analysis_date",
        "created_at",
    )

    search_fields = (
        "user__username",
        "stock__symbol",
        "stock__company_name",
    )

    readonly_fields = ("created_at",)