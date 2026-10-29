"""
Production Serializers
"""
from decimal import Decimal
from rest_framework import serializers
from drf_spectacular.utils import OpenApiExample, extend_schema_serializer
from .models import ProductionBatch, ProductionConsumption, ProductionOutput
from apps.inventory.serializers import InventoryLotSerializer


class ProductionConsumptionSerializer(serializers.ModelSerializer):
    batch_no = serializers.CharField(source='batch.batch_no', read_only=True)
    product_code = serializers.CharField(source='material_lot.product.code', read_only=True)
    product_name = serializers.CharField(source='material_lot.product.name', read_only=True)
    lot_batch_no = serializers.CharField(source='material_lot.batch_no', read_only=True)
    total_cost = serializers.SerializerMethodField()

    class Meta:
        model = ProductionConsumption
        fields = ('id', 'batch', 'batch_no', 'material_lot', 'lot_batch_no',
                  'product_code', 'product_name', 'qty_consumed',
                  'cost_at_consumption', 'total_cost', 'consumed_at')
        read_only_fields = ('id', 'cost_at_consumption', 'consumed_at')

    def get_total_cost(self, obj):
        return str(obj.total_cost)


class ProductionOutputSerializer(serializers.ModelSerializer):
    batch_no = serializers.CharField(source='batch.batch_no', read_only=True)
    product_code = serializers.CharField(source='product.code', read_only=True)
    lot_batch_no = serializers.CharField(source='lot.batch_no', read_only=True)
    lot_expiry = serializers.DateField(source='lot.expiry_date', read_only=True)

    class Meta:
        model = ProductionOutput
        fields = ('id', 'batch', 'batch_no', 'product', 'product_code',
                  'qty_produced', 'qty_waste', 'lot', 'lot_batch_no',
                  'lot_expiry', 'output_at')
        read_only_fields = ('id', 'lot', 'output_at')


class ProductionBatchSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source='product.code', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    efficiency = serializers.SerializerMethodField()
    total_consumption_cost = serializers.SerializerMethodField()
    consumptions_count = serializers.SerializerMethodField()

    class Meta:
        model = ProductionBatch
        fields = ('id', 'batch_no', 'product', 'product_code', 'product_name',
                  'planned_qty', 'actual_qty', 'waste_qty',
                  'start_at', 'end_at', 'status', 'weighted_avg_cost',
                  'efficiency', 'total_consumption_cost', 'consumptions_count',
                  'notes', 'created_at')
        read_only_fields = ('id', 'batch_no', 'actual_qty', 'waste_qty',
                          'weighted_avg_cost', 'start_at', 'end_at', 'created_at')

    def get_efficiency(self, obj):
        return round(obj.efficiency, 2)

    def get_total_consumption_cost(self, obj):
        return str(obj.total_consumption_cost)

    def get_consumptions_count(self, obj):
        return obj.consumptions.count()


class ProductionBatchDetailSerializer(ProductionBatchSerializer):
    consumptions = ProductionConsumptionSerializer(many=True, read_only=True)
    outputs = ProductionOutputSerializer(many=True, read_only=True)

    class Meta(ProductionBatchSerializer.Meta):
        fields = ProductionBatchSerializer.Meta.fields + ('consumptions', 'outputs')


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'بچ نمونه',
            summary='بچ تولید نان بربری',
            description='ساخت بچ ۱۰۰ عدد نان بربری',
            value={
                'product_id': 1,
                'planned_qty': '100',
                'notes': 'تولید روزانه صبح',
            },
            request_only=True,
        ),
    ]
)
class CreateBatchInputSerializer(serializers.Serializer):
    """input برای ساخت بچ تولید جدید"""
    product_id = serializers.IntegerField(help_text='شناسه محصول نهایی')
    planned_qty = serializers.DecimalField(
        max_digits=14, decimal_places=3,
        help_text='مقدار برنامه‌ریزی‌شده (مثلاً 100)',
    )
    notes = serializers.CharField(required=False, allow_blank=True)


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'مصرف نمونه',
            summary='مصرف ۵۰ کیلو آرد',
            description='ثبت مصرف ۵۰ کیلو از لات آرد',
            value={
                'batch_id': 1,
                'material_lot_id': 5,
                'qty': '50',
            },
            request_only=True,
        ),
    ]
)
class ConsumeMaterialInputSerializer(serializers.Serializer):
    """input برای ثبت مصرف مواد اولیه در بچ"""
    batch_id = serializers.IntegerField(help_text='شناسه بچ (در حال اجرا)')
    material_lot_id = serializers.IntegerField(
        help_text='شناسه لات ماده اولیه در انبار',
    )
    qty = serializers.DecimalField(
        max_digits=14, decimal_places=3,
        help_text='مقدار مصرف (مثلاً 50 کیلو)',
    )


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'تکمیل نمونه',
            summary='تکمیل بچ با ضایعات',
            description='تکمیل بچ: ۹۰ تولیدشده، ۱۰ ضایعات',
            value={
                'batch_id': 1,
                'actual_qty': '90',
                'waste_qty': '10',
            },
            request_only=True,
        ),
    ]
)
class CompleteBatchInputSerializer(serializers.Serializer):
    """input برای تکمیل بچ تولید"""
    batch_id = serializers.IntegerField(help_text='شناسه بچ در حال اجرا')
    actual_qty = serializers.DecimalField(
        max_digits=14, decimal_places=3,
        help_text='مقدار واقعی تولیدشده (مثلاً 90)',
    )
    waste_qty = serializers.DecimalField(
        max_digits=14, decimal_places=3,
        required=False, default=Decimal('0'),
        help_text='مقدار ضایعات (مثلاً 10)',
    )
