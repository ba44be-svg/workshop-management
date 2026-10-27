"""
Sales Views
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from core.permissions import IsManager, IsManagerOrAccountant, IsManagerOrDistributor
from .models import SalesHeader, ReturnHeader
from .serializers import (
    SalesHeaderSerializer, SalesDetailSerializer, ReturnHeaderSerializer,
    CreateSaleInputSerializer, CreateReturnInputSerializer,
)
from .services import SalesService


class SalesViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet برای مشاهده فروش‌ها"""
    queryset = SalesHeader.objects.filter(deleted_at__isnull=True)
    permission_classes = [IsAuthenticated]
    filterset_fields = ['store', 'sales_type', 'status', 'sale_date',
                        'distributor', 'dispatch']
    search_fields = ['sale_no', 'store__name', 'notes']
    ordering_fields = ['sale_date', 'total_amount', 'created_at']
    ordering = ['-sale_date']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SalesDetailSerializer
        return SalesHeaderSerializer

    @extend_schema(
        request=CreateSaleInputSerializer,
        responses=SalesDetailSerializer,
        description='ثبت فروش جدید با تخصیص FEFO خودکار. این endpoint هم امانی و هم قطعی را پشتیبانی می‌کند. '
                    'برای هر خط، لات به‌صورت خودکار بر اساس نزدیک‌ترین تاریخ انقضا تخصیص می‌یابد.',
        summary='ثبت فروش امانی/قطعی',
        tags=['sales'],
    )
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsManagerOrDistributor])
    def create_sale(self, request):
        """ثبت فروش جدید با تخصیص FEFO خودکار"""
        serializer = CreateSaleInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            sale = SalesService.create_sale(
                store_id=data['store_id'],
                sales_type=data['sales_type'],
                sale_date=data.get('sale_date'),
                lines=data['lines'],
                distributor_id=data.get('distributor_id'),
                dispatch_id=data.get('dispatch_id'),
                notes=data.get('notes', ''),
                created_by=request.user,
            )
            return Response(
                SalesDetailSerializer(sale, context={'request': request}).data,
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=['get'])
    def daily_report(self, request):
        """گزارش فروش روزانه"""
        from django.utils import timezone
        from django.db.models import Sum, Count, Q
        from datetime import timedelta

        date_str = request.query_params.get('date')
        if date_str:
            date = timezone.datetime.fromisoformat(date_str).date()
        else:
            date = timezone.now().date()

        sales = SalesHeader.objects.filter(
            sale_date=date,
            status=SalesHeader.SalesStatus.POSTED,
        )
        summary = sales.aggregate(
            total_amount=Sum('total_amount'),
            total_cost=Sum('total_cost'),
            count=Count('id'),
        )
        profit = (summary['total_amount'] or 0) - (summary['total_cost'] or 0)

        return Response({
            'date': date.isoformat(),
            'total_amount': str(summary['total_amount'] or 0),
            'total_cost': str(summary['total_cost'] or 0),
            'total_profit': str(profit),
            'sales_count': summary['count'],
            'consignment_count': sales.filter(
                sales_type=SalesHeader.SalesType.CONSIGNMENT
            ).count(),
            'firm_count': sales.filter(
                sales_type=SalesHeader.SalesType.FIRM
            ).count(),
        })

    @action(detail=False, methods=['get'])
    def store_balance(self, request):
        """مانده حساب یک فروشگاه"""
        store_id = request.query_params.get('store_id')
        if not store_id:
            return Response(
                {'detail': 'store_id لازم است'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        balance = SalesService.get_store_balance(int(store_id))
        return Response(balance)


class ReturnViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet برای مشاهده برگشت‌ها"""
    queryset = ReturnHeader.objects.filter(deleted_at__isnull=True)
    serializer_class = ReturnHeaderSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['store', 'status', 'return_date']
    search_fields = ['return_no', 'reason']
    ordering = ['-return_date']

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsManagerOrDistributor])
    def create_return(self, request):
        """ثبت برگشت جدید"""
        serializer = CreateReturnInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            ret = SalesService.create_return(
                store_id=data['store_id'],
                original_sale_id=data.get('original_sale_id'),
                lines=data['lines'],
                reason=data.get('reason', ''),
                return_date=data.get('return_date'),
                created_by=request.user,
            )
            return Response(
                ReturnHeaderSerializer(ret, context={'request': request}).data,
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
