"""
Sales Serializers
"""
from rest_framework import serializers
from .models import SalesHeader, SalesLine, ReturnHeader, ReturnLine


class SalesLineSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source='product.code', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    lot_batch_no = serializers.CharField(source='lot.batch_no', read_only=True)
    line_total = serializers.SerializerMethodField()
    line_cost = serializers.SerializerMethodField()
    line_profit = serializers.SerializerMethodField()

    class Meta:
        model = SalesLine
        fields = ('id', 'sale', 'product', 'product_code', 'product_name',
                  'lot', 'lot_batch_no', 'qty', 'unit_price', 'unit_cost',
                  'line_total', 'line_cost', 'line_profit')
        read_only_fields = ('id', 'sale', 'unit_cost')

    def get_line_total(self, obj):
        return str(obj.line_total)

    def get_line_cost(self, obj):
        return str(obj.line_cost)

    def get_line_profit(self, obj):
        return str(obj.line_profit)


class SalesHeaderSerializer(serializers.ModelSerializer):
    store_name = serializers.CharField(source='store.name', read_only=True)
    distributor_name = serializers.CharField(source='distributor.name', read_only=True, default='')
    total_profit = serializers.SerializerMethodField()
    lines_count = serializers.SerializerMethodField()

    class Meta:
        model = SalesHeader
        fields = ('id', 'sale_no', 'store', 'store_name', 'sale_date', 'sales_type',
                  'total_amount', 'total_cost', 'total_profit', 'status',
                  'distributor', 'distributor_name', 'dispatch', 'journal', 'tax_invoice',
                  'notes', 'lines_count', 'created_at')
        read_only_fields = ('id', 'sale_no', 'total_amount', 'total_cost',
                          'total_profit', 'journal', 'tax_invoice', 'created_at')

    def get_total_profit(self, obj):
        return str(obj.total_profit)

    def get_lines_count(self, obj):
        return obj.lines.count()


class SalesDetailSerializer(SalesHeaderSerializer):
    lines = SalesLineSerializer(many=True, read_only=True)

    class Meta(SalesHeaderSerializer.Meta):
        fields = SalesHeaderSerializer.Meta.fields + ('lines',)


class CreateSaleLineInputSerializer(serializers.Serializer):
    """input برای ساخت فروش"""
    product_id = serializers.IntegerField()
    qty = serializers.DecimalField(max_digits=14, decimal_places=3)
    unit_price = serializers.DecimalField(max_digits=18, decimal_places=4)
    warehouse_id = serializers.IntegerField(required=False)


class CreateSaleInputSerializer(serializers.Serializer):
    store_id = serializers.IntegerField()
    sales_type = serializers.ChoiceField(choices=SalesHeader.SalesType.choices)
    sale_date = serializers.DateField(required=False)
    distributor_id = serializers.IntegerField(required=False, allow_null=True)
    dispatch_id = serializers.IntegerField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    lines = CreateSaleLineInputSerializer(many=True)


class ReturnLineSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source='product.code', read_only=True)

    class Meta:
        model = ReturnLine
        fields = ('id', 'return_header', 'product', 'product_code', 'lot',
                  'qty', 'condition', 'notes')
        read_only_fields = ('id', 'return_header')


class ReturnHeaderSerializer(serializers.ModelSerializer):
    store_name = serializers.CharField(source='store.name', read_only=True)
    original_sale_no = serializers.CharField(source='original_sale.sale_no', read_only=True, default='')
    lines = ReturnLineSerializer(many=True, read_only=True)

    class Meta:
        model = ReturnHeader
        fields = ('id', 'return_no', 'store', 'store_name', 'return_date',
                  'original_sale', 'original_sale_no', 'total_qty', 'reason',
                  'status', 'journal', 'lines', 'created_at')
        read_only_fields = ('id', 'return_no', 'total_qty', 'journal', 'created_at')


class CreateReturnInputSerializer(serializers.Serializer):
    store_id = serializers.IntegerField()
    original_sale_id = serializers.IntegerField(required=False, allow_null=True)
    return_date = serializers.DateField(required=False)
    reason = serializers.CharField(required=False, allow_blank=True)
    lines = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
    )
