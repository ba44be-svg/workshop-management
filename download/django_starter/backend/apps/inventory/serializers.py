"""
Inventory Serializers
"""
from rest_framework import serializers
from .models import Warehouse, InventoryLot, InventoryMovement, StockBalance


class WarehouseSerializer(serializers.ModelSerializer):
    store_name = serializers.CharField(source='store.name', read_only=True, default='')
    store_code = serializers.CharField(source='store.code', read_only=True, default='')

    class Meta:
        model = Warehouse
        fields = ('id', 'code', 'name', 'type', 'store', 'store_name', 'store_code',
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
