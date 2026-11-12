from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import StockViewSet, LatestStockPriceView

router = DefaultRouter()

router.register(
    r"stocks",
    StockViewSet,
    basename="stock",
)

urlpatterns = [
    path(
        "stocks/<str:symbol>/latest/",
        LatestStockPriceView.as_view(),
        name="latest-stock-price",
    ),
]

urlpatterns += router.urls