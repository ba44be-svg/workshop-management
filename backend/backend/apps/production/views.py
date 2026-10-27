"""
Production Views
"""
from decimal import Decimal
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from core.permissions import IsManagerOrStorekeeper
from .models import ProductionBatch, ProductionConsumption, ProductionOutput
from .serializers import (
    ProductionBatchSerializer, ProductionBatchDetailSerializer,
    ProductionConsumptionSerializer, ProductionOutputSerializer,
    CreateBatchInputSerializer, ConsumeMaterialInputSerializer,
    CompleteBatchInputSerializer,
)
from .services import ProductionService


class ProductionBatchViewSet(viewsets.ModelViewSet):
    """ViewSet برای بچ‌های تولید"""
    queryset = ProductionBatch.objects.filter(deleted_at__isnull=True)
    permission_classes = [IsAuthenticated, IsManagerOrStorekeeper]
    filterset_fields = ['product', 'status', 'start_at', 'end_at']
    search_fields = ['batch_no', 'product__code', 'product__name', 'notes']
    ordering_fields = ['start_at', 'end_at', 'actual_qty', 'created_at']
    ordering = ['-start_at']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductionBatchDetailSerializer
        return ProductionBatchSerializer

    @extend_schema(
        request=CreateBatchInputSerializer,
        responses=ProductionBatchSerializer,
        summary='ساخت بچ تولید',
        description='ساخت یک بچ تولید جدید در وضعیت planned. پس از ساخت، باید با '
                    'endpoint start آن را شروع دهید، سپس consume_material را برای '
                    'ثبت مصرف مواد استفاده کنید و در نهایت complete را صدا بزنید.',
        tags=['production'],
    )
    @action(detail=False, methods=['post'])
    def create_batch(self, request):
        """ساخت بچ تولید جدید"""
        serializer = CreateBatchInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            batch = ProductionService.create_batch(
                product_id=serializer.validated_data['product_id'],
                planned_qty=serializer.validated_data['planned_qty'],
                notes=serializer.validated_data.get('notes', ''),
                created_by=request.user,
            )
            return Response(
                ProductionBatchSerializer(batch, context={'request': request}).data,
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @extend_schema(
        summary='شروع بچ تولید',
        description='تغییر وضعیت بچ از planned به in_progress. '
                    'فقط بچ‌های planned قابل شروع هستند.',
        tags=['production'],
        request=None,
    )
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """شروع بچ تولید"""
        try:
            batch = ProductionService.start_batch(
                batch_id=int(pk),
                started_by=request.user,
            )
            return Response(ProductionBatchSerializer(
                batch, context={'request': request}
            ).data)
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @extend_schema(
        request=ConsumeMaterialInputSerializer,
        responses=ProductionConsumptionSerializer,
        summary='ثبت مصرف مواد اولیه',
        description='کاهش موجودی لات ماده اولیه و ثبت هزینه لحظه‌ای. '
                    'بچ باید در وضعیت in_progress باشد.',
        tags=['production'],
    )
    @action(detail=False, methods=['post'])
    def consume_material(self, request):
        """ثبت مصرف مواد اولیه برای بچ"""
        serializer = ConsumeMaterialInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            consumption = ProductionService.consume_material(
                batch_id=serializer.validated_data['batch_id'],
                material_lot_id=serializer.validated_data['material_lot_id'],
                qty=serializer.validated_data['qty'],
                consumed_by=request.user,
            )
            return Response(
                ProductionConsumptionSerializer(
                    consumption, context={'request': request}
                ).data,
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @extend_schema(
        request=CompleteBatchInputSerializer,
        responses=ProductionBatchDetailSerializer,
        summary='تکمیل بچ تولید',
        description='تکمیل بچ، ساخت لات جدید برای محصول نهایی با بهای تمام‌شده '
                    'میانگین موزون، و ثبت ProductionOutput. این endpoint همچنین '
                    'یک حرکت ورود به انبار ثبت می‌کند.',
        tags=['production'],
    )
    @action(detail=False, methods=['post'])
    def complete(self, request):
        """تکمیل بچ تولید — ساخت لات خودکار"""
        serializer = CompleteBatchInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            batch = ProductionService.complete_batch(
                batch_id=serializer.validated_data['batch_id'],
                actual_qty=serializer.validated_data['actual_qty'],
                waste_qty=serializer.validated_data.get('waste_qty', Decimal('0')),
                completed_by=request.user,
            )
            return Response(ProductionBatchDetailSerializer(
                batch, context={'request': request}
            ).data)
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @extend_schema(
        summary='لغو بچ',
        description='لغو بچ. بچ‌های تکمیل‌شده قابل لغو نیستند.',
        tags=['production'],
        request=None,
    )
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """لغو بچ"""
        reason = request.data.get('reason', '')
        try:
            batch = ProductionService.cancel_batch(
                batch_id=int(pk),
                reason=reason,
                canceled_by=request.user,
            )
            return Response(ProductionBatchSerializer(
                batch, context={'request': request}
            ).data)
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @extend_schema(
        summary='گزارش تولید',
        description='گزارش تولید در یک بازه زمانی (پیش‌فرض: ۳۰ روز اخیر). '
                    'شامل تعداد بچ‌ها، مجموع تولید، ضایعات و راندمان.',
        tags=['production'],
    )
    @action(detail=False, methods=['get'])
    def report(self, request):
        """گزارش تولید"""
        from datetime import datetime
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        if date_from:
            date_from = datetime.fromisoformat(date_from).date()
        if date_to:
            date_to = datetime.fromisoformat(date_to).date()
        report = ProductionService.get_production_report(date_from, date_to)
        return Response(report)


class ProductionConsumptionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet فقط خواندنی برای مصرف‌های مواد"""
    queryset = ProductionConsumption.objects.all()
    serializer_class = ProductionConsumptionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['batch', 'material_lot']
    ordering = ['-consumed_at']


class ProductionOutputViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet فقط خواندنی برای خروج‌های تولید"""
    queryset = ProductionOutput.objects.all()
    serializer_class = ProductionOutputSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['batch', 'product', 'lot']
    ordering = ['-output_at']
