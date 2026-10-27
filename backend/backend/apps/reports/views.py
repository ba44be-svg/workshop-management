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

    # =========================================================
    # Week-5 Reports — 7 new actions
    # =========================================================

    @action(detail=False, methods=['get'])
    def store_receivables(self, request):
        """طلبکار از فروشگاه‌ها (فروش امانی تسویه‌نشده)"""
        days = int(request.query_params.get('days', 90))
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        return Response(ReportsService.store_receivables(
            days=days, start_date=start_date, end_date=end_date))

    @action(detail=False, methods=['get'])
    def store_stock(self, request):
        """موجودی کالا در انبارهای فروشگاه"""
        days = int(request.query_params.get('days', 30))
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        return Response(ReportsService.store_stock(
            days=days, start_date=start_date, end_date=end_date))

    @action(detail=False, methods=['get'])
    def distributor_stock(self, request):
        """موجودی نزد عوامل پخش"""
        days = int(request.query_params.get('days', 30))
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        return Response(ReportsService.distributor_stock(
            days=days, start_date=start_date, end_date=end_date))

    @action(detail=False, methods=['get'])
    def distributor_commission(self, request):
        """گزارش پورسانت عوامل پخش"""
        days = int(request.query_params.get('days', 30))
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        return Response(ReportsService.distributor_commission(
            days=days, start_date=start_date, end_date=end_date))

    @action(detail=False, methods=['get'])
    def waste_report_detailed(self, request):
        """گزارش تفصیلی ضایعات"""
        days = int(request.query_params.get('days', 30))
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        return Response(ReportsService.waste_report_detailed(
            days=days, start_date=start_date, end_date=end_date))

    @action(detail=False, methods=['get'])
    def near_expiry(self, request):
        """لات‌های نزدیک به انقضا"""
        days_threshold = int(request.query_params.get('days_threshold', 7))
        return Response(ReportsService.near_expiry(days_threshold=days_threshold))

    @action(detail=False, methods=['get'])
    def profit_report(self, request):
        """گزارش سود (گروه‌بندی بر اساس product/store/distributor)"""
        days = int(request.query_params.get('days', 30))
        group_by = request.query_params.get('group_by', 'product')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        return Response(ReportsService.profit_report(
            days=days, group_by=group_by,
            start_date=start_date, end_date=end_date))
