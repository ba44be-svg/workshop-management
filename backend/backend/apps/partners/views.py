"""
Partners Views
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core.permissions import IsManager, IsManagerOrAccountant, IsStoreOwner
from .models import Distributor, Store, Customer, PartnerCredit, LoyaltyPoint
from .serializers import (
    DistributorSerializer, StoreSerializer, CustomerSerializer,
    PartnerCreditSerializer, LoyaltyPointSerializer,
)


class DistributorViewSet(viewsets.ModelViewSet):
    """ViewSet برای عوامل پخش"""
    queryset = Distributor.objects.filter(deleted_at__isnull=True)
    serializer_class = DistributorSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['is_active', 'vehicle']
    search_fields = ['code', 'name', 'mobile']
    ordering = ['code']

    @action(detail=False, methods=['get'])
    def status(self, request):
        """گزارش وضعیت همه‌ی عوامل پخش — شامل مبلغ تحویلی، فروش، برگشتی، پورسانت"""
        from .services import DistributorStatusService
        result = DistributorStatusService.get_all_distributors_status()
        return Response({'count': len(result), 'results': result})

    @action(detail=True, methods=['get'])
    def detail_status(self, request, pk=None):
        """گزارش وضعیت یک عامل پخش خاص"""
        from .services import DistributorStatusService
        distributor = self.get_object()
        result = DistributorStatusService.get_distributor_status(distributor)
        return Response(result)


class StoreViewSet(viewsets.ModelViewSet):
    """ViewSet برای فروشگاه‌ها"""
    queryset = Store.objects.filter(deleted_at__isnull=True)
    serializer_class = StoreSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['distributor', 'tier', 'sales_model', 'is_active']
    search_fields = ['code', 'name', 'address', 'phone']
    ordering = ['code']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsManager()]

    @action(detail=False, methods=['get'])
    def by_tier(self, request):
        """گروه‌بندی فروشگاه‌ها بر اساس لایه وفاداری"""
        from django.db.models import Count
        result = Store.objects.filter(
            deleted_at__isnull=True, is_active=True,
        ).values('tier').annotate(
            count=Count('id'),
        ).order_by('tier')
        return Response({'results': list(result)})

    @action(detail=False, methods=['get'])
    def geo_points(self, request):
        """مختصات جغرافیایی فروشگاه‌ها (برای Heatmap)"""
        from apps.sales.models import SalesHeader
        from django.db.models import Sum
        from django.utils import timezone
        from datetime import timedelta

        # محدوده تاریخ (مثلاً ۳۰ روز اخیر)
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)

        stores = Store.objects.filter(
            deleted_at__isnull=True,
            is_active=True,
            geo_lat__isnull=False,
        )

        results = []
        for store in stores:
            total_sales = SalesHeader.objects.filter(
                store=store,
                sale_date__gte=start_date,
                sale_date__lte=end_date,
                status=SalesHeader.SalesStatus.POSTED,
            ).aggregate(total=Sum('total_amount'))['total'] or 0

            # شدت بر اساس میزان فروش
            if total_sales > 100000000:
                intensity = 'very_high'
            elif total_sales > 50000000:
                intensity = 'high'
            elif total_sales > 10000000:
                intensity = 'medium'
            else:
                intensity = 'low'

            results.append({
                'store_id': store.id,
                'name': store.name,
                'lat': float(store.geo_lat),
                'lng': float(store.geo_lng),
                'total_sales': str(total_sales),
                'intensity': intensity,
                'tier': store.tier,
            })

        return Response({'results': results})

    @action(detail=True, methods=['get'])
    def balance(self, request, pk=None):
        """مانده حساب یک فروشگاه"""
        store = self.get_object()
        try:
            credit = store.credits.first()
            data = {
                'store_id': store.id,
                'credit_limit': str(store.credit_limit),
                'current_credit': str(store.current_credit),
                'available_credit': str(store.available_credit),
                'balance': str(credit.balance) if credit else '0',
                'in_credit_limit': store.available_credit > 0,
            }
        except Exception:
            data = {
                'store_id': store.id,
                'error': 'اطلاعات اعتبار در دسترس نیست',
            }
        return Response(data)


class CustomerViewSet(viewsets.ModelViewSet):
    """ViewSet برای مشتریان"""
    queryset = Customer.objects.filter(deleted_at__isnull=True)
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['type', 'platform', 'is_active']
    search_fields = ['name', 'phone', 'platform_user_id']
    ordering = ['name']


class LoyaltyPointViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet برای مشاهده تراکنش‌های وفاداری"""
    queryset = LoyaltyPoint.objects.all()
    serializer_class = LoyaltyPointSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['store', 'reason']
    ordering = ['-created_at']
