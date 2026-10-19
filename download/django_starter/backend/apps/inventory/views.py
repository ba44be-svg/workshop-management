"""
Inventory Views — شامل endpoint FEFO (مهم‌ترین endpoint)
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from core.permissions import IsManager, IsManagerOrStorekeeper, IsDistributor
from .models import Warehouse, InventoryLot, InventoryMovement, StockBalance
from .serializers import (
    WarehouseSerializer, InventoryLotSerializer, InventoryMovementSerializer,
    StockBalanceSerializer, FEFOAllocationRequestSerializer,
    FEFOAllocationResponseSerializer,
)
from .services.fefo_service import FEFOService


class WarehouseViewSet(viewsets.ModelViewSet):
    """ViewSet برای انبارها"""
    queryset = Warehouse.objects.filter(deleted_at__isnull=True)
    serializer_class = WarehouseSerializer
    permission_classes = [IsAuthenticated, IsManagerOrStorekeeper]
    filterset_fields = ['type', 'store', 'is_active']
    search_fields = ['code', 'name']
    ordering = ['code']


class InventoryLotViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet فقط خواندنی برای لات‌های انبار"""
    queryset = InventoryLot.objects.filter(deleted_at__isnull=True)
    serializer_class = InventoryLotSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['product', 'warehouse', 'status']
    search_fields = ['batch_no']
    ordering_fields = ['expiry_date', 'production_date', 'current_qty']
    ordering = ['expiry_date']

    @action(detail=False, methods=['get'])
    def near_expiry(self, request):
        """لات‌های نزدیک به انقضا (۵ روز آینده)"""
        days = int(request.query_params.get('days', 5))
        lots = FEFOService.find_near_expiry_lots(days_threshold=days)
        page = self.paginate_queryset(lots)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(lots, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def trace(self, request, pk=None):
        """ردیابی تاریخچه کامل یک لات (Trace-back)"""
        result = FEFOService.trace_lot_history(int(pk))
        return Response(result)


class InventoryMovementViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet فقط خواندنی برای حرکت‌های انبار"""
    queryset = InventoryMovement.objects.all()
    serializer_class = InventoryMovementSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['lot', 'product', 'warehouse', 'movement_type',
                        'ref_doc_type', 'ref_doc_id']
    ordering_fields = ['created_at', 'qty']
    ordering = ['-created_at']


class StockBalanceViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet فقط خواندنی برای موجودی تجمیعی"""
    queryset = StockBalance.objects.all()
    serializer_class = StockBalanceSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['product', 'warehouse']
    search_fields = ['product__code', 'product__name']
    ordering_fields = ['total_qty', 'total_value', 'updated_at']
    ordering = ['-updated_at']

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """محصولات کم‌موجودی"""
        threshold = int(request.query_params.get('threshold', 10))
        balances = StockBalance.objects.filter(total_qty__lt=threshold).select_related(
            'product', 'warehouse'
        )
        results = [
            {
                'product_id': b.product.id,
                'product_code': b.product.code,
                'product_name': b.product.name,
                'warehouse_id': b.warehouse.id,
                'warehouse_code': b.warehouse.code,
                'total_qty': str(b.total_qty),
                'threshold': threshold,
            }
            for b in balances
        ]
        return Response({'results': results, 'threshold': threshold})

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """خلاصه موجودی کلی"""
        from django.db.models import Sum
        total_qty = StockBalance.objects.aggregate(total=Sum('total_qty'))['total'] or 0
        total_value = StockBalance.objects.aggregate(total=Sum('total_value'))['total'] or 0
        return Response({
            'total_qty': str(total_qty),
            'total_value': str(total_value),
            'products_count': StockBalance.objects.values('product').distinct().count(),
            'warehouses_count': StockBalance.objects.values('warehouse').distinct().count(),
        })


class FEFOViewSet(viewsets.ViewSet):
    """ViewSet برای عملیات FEFO"""

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def allocate(self, request):
        """
        تخصیص لات‌ها بر اساس FEFO.
        POST /api/inventory/allocate-fefo/
        """
        from rest_framework.decorators import api_view, permission_classes
        serializer = FEFOAllocationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            result = FEFOService.allocate_lots(
                product_id=data['product_id'],
                warehouse_id=data['warehouse_id'],
                qty_needed=data['qty'],
                sale_date=data.get('sale_date'),
            )
            response_serializer = FEFOAllocationResponseSerializer({
                'allocated': result.allocated,
                'total_allocated_qty': result.total_allocated_qty,
                'allocations': [
                    {
                        'lot_id': a.lot_id,
                        'qty': a.qty,
                        'unit_cost': a.unit_cost,
                        'expiry_date': a.expiry_date,
                        'days_to_expiry': a.days_to_expiry,
                        'batch_no': a.batch_no,
                    }
                    for a in result.allocations
                ],
                'warning': result.warning,
            })
            return Response(response_serializer.data)
        except Exception as e:
            return Response(
                {'detail': str(e), 'allocated': False},
                status=status.HTTP_400_BAD_REQUEST,
            )
