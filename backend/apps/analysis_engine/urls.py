from django.urls import path

from .views import StockAnalysisView

urlpatterns = [
    path(
        "stocks/<str:symbol>/",
        StockAnalysisView.as_view(),
        name="stock-analysis",
    ),
]