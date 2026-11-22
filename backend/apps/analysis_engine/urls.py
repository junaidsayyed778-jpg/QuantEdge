from django.urls import path

from .views import StockAnalysisView, AnalysisHistoryView

urlpatterns = [
    path(
        "stocks/<str:symbol>/",
        StockAnalysisView.as_view(),
        name="stock-analysis",
    ),
    path(
        "history/",
        AnalysisHistoryView.as_view(),
        name="analysis-history",
    ),
]