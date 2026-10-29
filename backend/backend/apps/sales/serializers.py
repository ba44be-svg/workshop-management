"""
Sales Serializers
"""
from rest_framework import serializers
from drf_spectacular.utils import OpenApiExample, extend_schema_serializer
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
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    sales_type_display = serializers.CharField(source='get_sales_type_display', read_only=True)

    class Meta:
        model = SalesHeader
        fields = ('id', 'sale_no', 'store', 'store_name', 'sale_date', 'sales_type',
                  'sales_type_display', 'payment_method', 'payment_method_display',
                  'paid_amount',
                  'total_amount', 'total_cost', 'total_profit', 'status', 'status_display',
                  'distributor', 'distributor_name', 'dispatch', 'journal', 'tax_invoice',
                  'notes', 'lines_count', 'created_at')
        read_only_fields = ('id', 'sale_no', 'total_amount', 'total_cost',
                          'total_profit', 'journal', 'tax_invoice', 'created_at',
                          'payment_method_display', 'status_display', 'sales_type_display')

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
    product_id = serializers.IntegerField(help_text='شناسه محصول')
    qty = serializers.DecimalField(
        max_digits=14, decimal_places=3,
        help_text='مقدار فروش (مثلاً 30)',
    )
    unit_price = serializers.DecimalField(
        max_digits=18, decimal_places=4,
        help_text='قیمت واحد به ریال (مثلاً 50000.0000)',
    )
    warehouse_id = serializers.IntegerField(
        required=False,
        help_text='شناسه انبار. اگر خالی باشد، انبار اصلی پیش‌فرض است.',
    )


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'فروش امانی نمونه',
            summary='یک سند امانی با ۲ خط',
            description='نمونه ساخت فروش امانی ۲ خط محصول',
            value={
                'store_id': 1,
                'sales_type': 'consignment',
                'notes': 'فروش صبح',
                'lines': [
                    {'product_id': 1, 'qty': '30', 'unit_price': '50000.0000'},
                    {'product_id': 2, 'qty': '20', 'unit_price': '70000.0000'},
                ],
            },
            request_only=True,
        ),
        OpenApiExample(
            'فروش قطعی نمونه',
            summary='یک سند قطعی تک خط',
            description='نمونه فروش قطعی تک خط محصول',
            value={
                'store_id': 2,
                'sales_type': 'firm',
                'lines': [
                    {'product_id': 5, 'qty': '10', 'unit_price': '120000.0000'},
                ],
            },
            request_only=True,
        ),
    ]
)
class CreateSaleInputSerializer(serializers.Serializer):
    """input برای ساخت فروش امانی/قطعی"""
    store_id = serializers.IntegerField(help_text='شناسه فروشگاه مقصد')
    sales_type = serializers.ChoiceField(
        choices=SalesHeader.SalesType.choices,
        help_text='consignment = امانی، firm = قطعی',
    )
    payment_method = serializers.ChoiceField(
        choices=SalesHeader.PAYMENT_CHOICES,
        required=False,
        default='cash',
        help_text='نحوه دریافت وجه (cash/check/card/bank_transfer)',
    )
    paid_amount = serializers.DecimalField(
        max_digits=18, decimal_places=4,
        required=False,
        default='0',
        help_text='مبلغ دریافت‌شده (ریال)',
    )
    sale_date = serializers.DateField(
        required=False,
        help_text='تاریخ فروش (YYYY-MM-DD). امروز پیش‌فرض.',
    )
    distributor_id = serializers.IntegerField(
        required=False, allow_null=True,
        help_text='شناسه عامل پخش (اختیاری)',
    )
    dispatch_id = serializers.IntegerField(
        required=False, allow_null=True,
        help_text='شناسه سند پخش مرتبط (اختیاری)',
    )
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
