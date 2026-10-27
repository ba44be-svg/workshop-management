"""
Store Portal Serializers
"""
from rest_framework import serializers
from .models import StoreOrder, StoreOrderLine, StoreNotification, StoreDashboard


class StoreOrderLineSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source='product.code', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = StoreOrderLine
        fields = ('id', 'order', 'product', 'product_code', 'product_name',
                  'qty', 'unit_price', 'line_total', 'is_smart_suggestion', 'notes')
        read_only_fields = ('id', 'order', 'unit_price', 'line_total')

    def get_line_total(self, obj):
        return str(obj.line_total)


class StoreOrderSerializer(serializers.ModelSerializer):
    store_name = serializers.CharField(source='store.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_status_display = serializers.CharField(
        source='get_payment_status_display', read_only=True
    )
    lines_count = serializers.SerializerMethodField()

    class Meta:
        model = StoreOrder
        fields = ('id', 'order_no', 'store', 'store_name', 'order_date',
                  'status', 'status_display', 'total_amount', 'total_qty',
                  'payment_status', 'payment_status_display',
                  'expected_delivery', 'dispatch', 'notes', 'lines_count',
                  'created_at')
        read_only_fields = ('id', 'order_no', 'total_amount', 'total_qty',
                          'dispatch', 'created_at')

    def get_lines_count(self, obj):
        return obj.lines.count()


class StoreOrderDetailSerializer(StoreOrderSerializer):
    lines = StoreOrderLineSerializer(many=True, read_only=True)

    class Meta(StoreOrderSerializer.Meta):
        fields = StoreOrderSerializer.Meta.fields + ('lines',)


class CreateOrderInputSerializer(serializers.Serializer):
    lines = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
    )
    notes = serializers.CharField(required=False, allow_blank=True)
    expected_delivery = serializers.DateField(required=False, allow_null=True)
    delivery_address = serializers.CharField(required=False, allow_blank=True)


class StoreNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreNotification
        fields = '__all__'
        read_only_fields = ('id', 'store', 'created_at')


class StoreDashboardSerializer(serializers.ModelSerializer):
    store_name = serializers.CharField(source='store.name', read_only=True)

    class Meta:
        model = StoreDashboard
        fields = '__all__'
        read_only_fields = ('id', 'store', 'updated_at')
