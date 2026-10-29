"""
Inventory Serializers
"""
from rest_framework import serializers
from .models import Warehouse, InventoryLot, InventoryMovement, StockBalance


class WarehouseSerializer(serializers.ModelSerializer):
    store_name = serializers.CharField(source='store.name', read_only=True, default='')
    store_code = serializers.CharField(source='store.code', read_only=True, default='')
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    contractor_name = serializers.CharField(source='contractor.name', read_only=True, default='')
    contractor_code = serializers.CharField(source='contractor.code', read_only=True, default='')

    class Meta:
        model = Warehouse
        fields = ('id', 'code', 'name', 'type', 'type_display',
                  'store', 'store_name', 'store_code',
                  'contractor', 'contractor_name', 'contractor_code',
                  'address', 'is_active', 'created_at')
        read_only_fields = ('id', 'created_at')


class InventoryLotSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source='product.code', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    warehouse_code = serializers.CharField(source='warehouse.code', read_only=True)
    days_to_expiry = serializers.SerializerMethodField()

    class Meta:
        model = InventoryLot
        fields = ('id', 'product', 'product_code', 'product_name',
                  'warehouse', 'warehouse_code', 'batch_no',
                  'production_date', 'expiry_date', 'initial_qty', 'current_qty',
                  'weighted_avg_cost', 'status', 'production_batch',
                  'days_to_expiry', 'created_at')
        read_only_fields = ('id', 'created_at', 'weighted_avg_cost')

    def get_days_to_expiry(self, obj):
        return obj.days_to_expiry


class InventoryMovementSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source='product.code', read_only=True)
    lot_batch_no = serializers.CharField(source='lot.batch_no', read_only=True)

    class Meta:
        model = InventoryMovement
        fields = ('id', 'lot', 'lot_batch_no', 'product', 'product_code',
                  'warehouse', 'movement_type', 'qty', 'unit_cost',
                  'ref_doc_type', 'ref_doc_id', 'created_at')
        read_only_fields = ('id', 'created_at')


class StockBalanceSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source='product.code', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    warehouse_code = serializers.CharField(source='warehouse.code', read_only=True)

    class Meta:
        model = StockBalance
        fields = ('id', 'product', 'product_code', 'product_name',
                  'warehouse', 'warehouse_code', 'total_qty', 'total_value',
                  'last_lot', 'updated_at')
        read_only_fields = ('id', 'updated_at')


class FEFOAllocationRequestSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    warehouse_id = serializers.IntegerField()
    qty = serializers.DecimalField(max_digits=14, decimal_places=3)
    sale_date = serializers.DateField(required=False)


class FEFOAllocationItemSerializer(serializers.Serializer):
    lot_id = serializers.IntegerField()
    qty = serializers.DecimalField(max_digits=14, decimal_places=3)
    unit_cost = serializers.DecimalField(max_digits=18, decimal_places=4)
    expiry_date = serializers.CharField()
    days_to_expiry = serializers.IntegerField()
    batch_no = serializers.CharField()


class FEFOAllocationResponseSerializer(serializers.Serializer):
    allocated = serializers.BooleanField()
    total_allocated_qty = serializers.DecimalField(max_digits=14, decimal_places=3)
    allocations = FEFOAllocationItemSerializer(many=True)
    warning = serializers.CharField(required=False, allow_null=True)


# ============================================================================
# Waste serializers
# ============================================================================

class WasteLineSerializer(serializers.ModelSerializer):
    """serializer برای خطوط ضایعات"""
    product_code = serializers.CharField(source='product.code', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    lot_batch_no = serializers.CharField(source='lot.batch_no', read_only=True, default='')
    condition_display = serializers.CharField(source='get_condition_display', read_only=True)
    line_total = serializers.SerializerMethodField()

    class Meta:
        from .models import WasteLine
        model = WasteLine
        fields = ('id', 'waste_document', 'product', 'product_code', 'product_name',
                  'lot', 'lot_batch_no', 'qty', 'unit_cost', 'line_total',
                  'condition', 'condition_display', 'description')
        read_only_fields = ('id', 'line_total')

    def get_line_total(self, obj):
        return str(obj.line_total)


class WasteDocumentSerializer(serializers.ModelSerializer):
    """serializer برای سند ضایعات"""
    waste_type_display = serializers.CharField(source='get_waste_type_display', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True, default='')
    store_name = serializers.CharField(source='store.name', read_only=True, default='')
    distributor_name = serializers.CharField(source='distributor.name', read_only=True, default='')
    lines_count = serializers.SerializerMethodField()

    class Meta:
        from .models import WasteDocument
        model = WasteDocument
        fields = ('id', 'waste_no', 'waste_type', 'waste_type_display',
                  'warehouse', 'warehouse_name',
                  'store', 'store_name',
                  'distributor', 'distributor_name',
                  'waste_date', 'reason', 'total_value', 'status',
                  'lines_count', 'created_at')
        read_only_fields = ('id', 'waste_no', 'total_value', 'lines_count', 'created_at')

    def get_lines_count(self, obj):
        return obj.lines.count()


class WasteDocumentDetailSerializer(WasteDocumentSerializer):
    """serializer برای جزئیات سند ضایعات (با lines)"""
    lines = WasteLineSerializer(many=True, read_only=True)

    class Meta(WasteDocumentSerializer.Meta):
        fields = WasteDocumentSerializer.Meta.fields + ('lines',)


class CreateWasteLineInputSerializer(serializers.Serializer):
    """input برای خط ضایعات"""
    product_id = serializers.IntegerField()
    qty = serializers.DecimalField(max_digits=14, decimal_places=3)
    unit_cost = serializers.DecimalField(max_digits=18, decimal_places=4, required=False, default=0)
    condition = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)


class CreateWasteInputSerializer(serializers.Serializer):
    """input برای ساخت سند ضایعات"""
    waste_type = serializers.ChoiceField(
        choices=['store', 'warehouse', 'distributor'],
        help_text='store = فروشگاه، warehouse = انبار، distributor = عامل پخش',
    )
    store_id = serializers.IntegerField(required=False, allow_null=True)
    warehouse_id = serializers.IntegerField(required=False, allow_null=True)
    distributor_id = serializers.IntegerField(required=False, allow_null=True)
    waste_date = serializers.DateField(required=False)
    reason = serializers.CharField(required=False, allow_blank=True)
    lines = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
    )
