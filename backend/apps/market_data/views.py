from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, APIException
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import PageNumberPagination

from .models import Stock
from .serializers import StockSerializer
from .services.latest_price import LatestPriceService


class StockPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class StockViewSet(viewsets.ModelViewSet):

    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    pagination_class = StockPagination

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    ]

    filterset_fields = ["symbol", "exchange", "sector"]

    search_fields = [
        "symbol",
        "company_name",
        "exchange",
        "sector",
    ]

    ordering_fields = [
        "symbol",
        "company_name",
        "exchange",
        "sector",
    ]

    ordering = ["symbol"]

    def get_permissions(self):

        if self.action in [
            "create",
            "update",
            "partial_update",
            "destroy",
        ]:
            return [IsAdminUser()]

        return [IsAuthenticated()]


class LatestStockPriceView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, symbol):

        try:
            result = LatestPriceService().get_stock_latest_price(symbol)

            return Response({
                "success": True,
                "data": result,
            }, status=status.HTTP_200_OK)

        except Stock.DoesNotExist:
            raise NotFound(
                f"Active NSE stock '{symbol}' was not found."
            )

        except ValueError as error:
            raise APIException(
                f"Unable to fetch latest price: {error}"
            )