"""
Reports Views
"""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core.permissions import IsManager
from .services import ReportsService


class ReportsViewSet(viewsets.ViewSet):
    """ViewSet برای گزارش‌های تحلیلی و داشبورد"""

    permission_classes = [IsAuthenticated, IsManager]

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """داشبورد بلادرنگ مدیر"""
        days = int(request.query_params.get('days', 30))
        summary = ReportsService.get_dashboard_summary(days=days)
        return Response(summary)

    @action(detail=False, methods=['get'])
    def geo_heatmap(self, request):
        """نقشه جغرافیایی فروش (Heatmap)"""
        days = int(request.query_params.get('days', 30))
        results = ReportsService.get_geo_heatmap(days=days)
        return Response({'results': results, 'days': days})

    @action(detail=False, methods=['get'])
    def waste_report(self, request):
        """گزارش ضایعات تولید"""
        days = int(request.query_params.get('days', 30))
        report = ReportsService.get_waste_report(days=days)
        return Response(report)

    @action(detail=False, methods=['get'])
    def top_products(self, request):
        """محصولات پرفروش"""
        days = int(request.query_params.get('days', 30))
        limit = int(request.query_params.get('limit', 20))
        results = ReportsService.get_top_products(days=days, limit=limit)
        return Response({'results': results, 'days': days})

    @action(detail=False, methods=['get'])
    def top_stores(self, request):
        """فروشگاه‌های پرفروش"""
        days = int(request.query_params.get('days', 30))
        limit = int(request.query_params.get('limit', 20))
        results = ReportsService.get_top_stores(days=days, limit=limit)
        return Response({'results': results, 'days': days})

    @action(detail=False, methods=['get'])
    def top_distributors(self, request):
        """عوامل پخش برتر"""
        days = int(request.query_params.get('days', 30))
        limit = int(request.query_params.get('limit', 10))
        results = ReportsService.get_top_distributors(days=days, limit=limit)
        return Response({'results': results, 'days': days})

    @action(detail=False, methods=['get'])
    def sales_trend(self, request):
        """روند فروش روزانه"""
        days = int(request.query_params.get('days', 30))
        results = ReportsService.get_sales_trend(days=days)
        return Response({'results': results, 'days': days})
