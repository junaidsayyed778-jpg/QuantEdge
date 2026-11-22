from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .services.stock_analysis import analyze_stock
from .services.analysis_history import save_analysis
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination

from .models import StockAnalysis
from .serializers import AnalysisHistorySerializer

from rest_framework.generics import RetrieveAPIView

from .serializers import AnalysisDetailSerializer
class StockAnalysisView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, symbol):
        try:
            result = analyze_stock(symbol)

            analysis, created = save_analysis(
                request.user,
                result,
            )

            result["history"] = {
                "analysis_id": analysis.id,
                "saved": True,
                "created": created,
            }

            return Response(result)

        except ValueError as error:
            return Response(
                {"error": str(error)},
                status=404,
            )
            
class AnalysisHistoryPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50
    
class AnalysisHistoryView(ListAPIView):
    serializer_class = AnalysisHistorySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = AnalysisHistoryPagination
    
    def get_queryset(self):
        return (
            StockAnalysis.objects
            .filter(user=self.request.user)
            .select_related("stock")
            .order_by("-created_at")
        )
        
class AnalysisHistoryDetailView(RetrieveAPIView):
    serializer_class = AnalysisDetailSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return(
            StockAnalysis.objects
            .filter(user=self.request.user)
            .select_related("stock")
        )