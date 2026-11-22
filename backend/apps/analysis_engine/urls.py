from django.urls import path

from .views import StockAnalysisView, AnalysisHistoryView, AnalysisHistoryDetailView

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
    path(
    "history/<int:pk>/",
    AnalysisHistoryDetailView.as_view(),
    name="analysis-history-detail",
),
]