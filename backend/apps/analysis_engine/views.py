from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .services.stock_analysis import analyze_stock
from .services.analysis_history import save_analysis

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