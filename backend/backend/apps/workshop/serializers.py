"""
Workshop Serializers
"""
from rest_framework import serializers
from .models import (
    Contractor, Employee, PurchaseHeader, PurchaseLine,
    PurchaseReturn, PurchaseReturnLine,
    WorkshopIssue, WorkshopIssueLine,
    WorkshopReturn, WorkshopReturnLine,
)


class ContractorSerializer(serializers.ModelSerializer):
    detail_account_code = serializers.CharField(
        source='detail_account.code', read_only=True, default=''
    )
    warehouses_count = serializers.SerializerMethodField()

    class Meta:
        model = Contractor
        fields = ('id', 'code', 'name', 'national_id', 'mobile', 'phone',
                  'address', 'workshop_name', 'is_active',
                  'detail_account', 'detail_account_code',
                  'warehouses_count', 'created_at')
        read_only_fields = ('id', 'detail_account', 'detail_account_code',
                            'warehouses_count', 'created_at')

    def get_warehouses_count(self, obj):
        return obj.warehouses.count()


class EmployeeSerializer(serializers.ModelSerializer):
    """Serializer برای مدل کارکنان (Employee)."""
    full_name = serializers.CharField(read_only=True)
    workshop_code = serializers.CharField(source='workshop.code', read_only=True, default='')
    workshop_name = serializers.CharField(source='workshop.name', read_only=True, default='')

    class Meta:
        model = Employee
        fields = ('id', 'code', 'first_name', 'last_name', 'full_name',
                  'national_id', 'mobile', 'phone', 'position',
                  'workshop', 'workshop_code', 'workshop_name',
                  'hire_date', 'is_active', 'created_at')
        read_only_fields = ('id', 'full_name', 'workshop_code', 'workshop_name',
                            'created_at')


class PurchaseLineSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source='product.code', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = PurchaseLine
        fields = ('id', 'purchase', 'product', 'product_code', 'product_name',
                  'qty', 'unit_price', 'unit_cost', 'shelf_life_days',
                  'expiry_date', 'lot_no', 'line_total', 'created_at')
        read_only_fields = ('id', 'unit_cost', 'lot_no', 'line_total', 'created_at')


class PurchaseHeaderSerializer(serializers.ModelSerializer):
    contractor_name = serializers.CharField(source='contractor.name', read_only=True, default='')
    warehouse_code = serializers.CharField(source='warehouse.code', read_only=True, default='')
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True, default='')
    cash_account_code = serializers.CharField(source='cash_account.code', read_only=True, default='')
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    lines_count = serializers.SerializerMethodField()
    journal_no = serializers.CharField(source='journal.journal_no', read_only=True, default='')

    class Meta:
        model = PurchaseHeader
        fields = ('id', 'purchase_no', 'purchase_date', 'contractor', 'contractor_name',
                  'warehouse', 'warehouse_code', 'warehouse_name',
                  'cash_account', 'cash_account_code',
                  'total_amount', 'total_qty', 'notes', 'journal', 'journal_no',
                  'status', 'status_display', 'lines_count', 'created_at')
        read_only_fields = ('id', 'total_amount', 'total_qty', 'journal',
                            'lines_count', 'created_at')

    def get_lines_count(self, obj):
        return obj.lines.count()


class PurchaseDetailSerializer(PurchaseHeaderSerializer):
    lines = PurchaseLineSerializer(many=True, read_only=True)

    class Meta(PurchaseHeaderSerializer.Meta):
        fields = PurchaseHeaderSerializer.Meta.fields + ('lines',)


class CreatePurchaseLineInputSerializer(serializers.Serializer):
    # پشتیبانی از دو حالت:
    # ۱) محصول موجود: product_id ارسال شود
    # ۲) محصول جدید: product_name (و اختیاری product_code) ارسال شود
    product_id = serializers.IntegerField(required=False, allow_null=True)
    product_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    product_code = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    qty = serializers.DecimalField(max_digits=14, decimal_places=3)
    unit_price = serializers.DecimalField(max_digits=18, decimal_places=4)
    shelf_life_days = serializers.IntegerField(required=False, default=15)
    expiry_date = serializers.DateField(required=False, allow_null=True)
    lot_no = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    unit_id = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, attrs):
        # حداقل یکی از product_id یا product_name باید ارسال شود
        if not attrs.get('product_id') and not attrs.get('product_name'):
            raise serializers.ValidationError(
                'یا product_id یا product_name باید ارسال شود.'
            )
        return attrs


class CreatePurchaseInputSerializer(serializers.Serializer):
    # purchase_no اختیاری است — اگر ارسال نشود، خود سرویس تولید می‌کند
    purchase_no = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    purchase_date = serializers.DateField()
    # هم فیلدهای با _id و هم بدون _id پذیرفته می‌شوند (برای هماهنگی با فرانت‌اند)
    contractor_id = serializers.IntegerField(required=False, allow_null=True)
    contractor = serializers.IntegerField(required=False, allow_null=True)
    warehouse_id = serializers.IntegerField(required=False, allow_null=True)
    warehouse = serializers.IntegerField(required=False, allow_null=True)
    cash_account_id = serializers.IntegerField(required=False, allow_null=True)
    cash_account = serializers.IntegerField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, default='')
    lines = serializers.ListField(
        child=CreatePurchaseLineInputSerializer(),
        min_length=1,
    )

    def validate(self, attrs):
        # نرمال‌سازی: اگر فیلدهای بدون _id ارسال شده، به _id تبدیل کن
        if attrs.get('contractor_id') is None and attrs.get('contractor') is not None:
            attrs['contractor_id'] = attrs['contractor']
        if attrs.get('warehouse_id') is None and attrs.get('warehouse') is not None:
            attrs['warehouse_id'] = attrs['warehouse']
        if attrs.get('cash_account_id') is None and attrs.get('cash_account') is not None:
            attrs['cash_account_id'] = attrs['cash_account']
        # اعتبارسنجی نهایی
        if attrs.get('contractor_id') is None:
            raise serializers.ValidationError({'contractor': 'این فیلد لازم است.'})
        if attrs.get('warehouse_id') is None:
            raise serializers.ValidationError({'warehouse': 'این فیلد لازم است.'})
        if attrs.get('cash_account_id') is None:
            raise serializers.ValidationError({'cash_account': 'این فیلد لازم است.'})
        return attrs


# ============================================================================
# WorkshopIssue serializers
# ============================================================================

class WorkshopIssueLineSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source='product.code', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    lot_batch_no = serializers.CharField(source='lot.batch_no', read_only=True)

    class Meta:
        model = WorkshopIssueLine
        fields = ('id', 'issue', 'product', 'product_code', 'product_name',
                  'lot', 'lot_batch_no', 'qty', 'unit_cost', 'line_total',
                  'created_at')
        read_only_fields = ('id', 'unit_cost', 'line_total', 'created_at')


class WorkshopIssueSerializer(serializers.ModelSerializer):
    contractor_name = serializers.CharField(source='contractor.name', read_only=True, default='')
    employee_name = serializers.CharField(source='employee.full_name', read_only=True, default='')
    from_warehouse_code = serializers.CharField(source='from_warehouse.code', read_only=True, default='')
    to_warehouse_code = serializers.CharField(source='to_warehouse.code', read_only=True, default='')
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    lines_count = serializers.SerializerMethodField()
    journal_no = serializers.CharField(source='journal.journal_no', read_only=True, default='')

    class Meta:
        model = WorkshopIssue
        fields = ('id', 'issue_no', 'issue_date', 'contractor', 'contractor_name',
                  'employee', 'employee_name',
                  'from_warehouse', 'from_warehouse_code',
                  'to_warehouse', 'to_warehouse_code',
                  'production_batch', 'total_qty', 'total_value',
                  'notes', 'journal', 'journal_no',
                  'status', 'status_display', 'lines_count', 'created_at')
        read_only_fields = ('id', 'total_qty', 'total_value', 'journal',
                            'lines_count', 'created_at')

    def get_lines_count(self, obj):
        return obj.lines.count()


class WorkshopIssueDetailSerializer(WorkshopIssueSerializer):
    lines = WorkshopIssueLineSerializer(many=True, read_only=True)

    class Meta(WorkshopIssueSerializer.Meta):
        fields = WorkshopIssueSerializer.Meta.fields + ('lines',)


class CreateIssueLineInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    qty = serializers.DecimalField(max_digits=14, decimal_places=3)


class CreateIssueInputSerializer(serializers.Serializer):
    issue_no = serializers.CharField(max_length=50)
    issue_date = serializers.DateField()
    contractor_id = serializers.IntegerField(required=False, allow_null=True)
    employee_id = serializers.IntegerField(required=False, allow_null=True)
    from_warehouse_id = serializers.IntegerField()
    to_warehouse_id = serializers.IntegerField()
    production_batch_id = serializers.IntegerField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, default='')
    lines = serializers.ListField(
        child=CreateIssueLineInputSerializer(),
        min_length=1,
    )


# ============================================================================
# WorkshopReturn serializers
# ============================================================================

class WorkshopReturnLineSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source='issue_line.product.code', read_only=True)
    product_name = serializers.CharField(source='issue_line.product.name', read_only=True)
    lot_batch_no = serializers.CharField(source='issue_line.lot.batch_no', read_only=True, default='')

    class Meta:
        model = WorkshopReturnLine
        fields = ('id', 'return_doc', 'issue_line', 'product_code', 'product_name',
                  'lot_batch_no', 'qty', 'unit_cost', 'line_total', 'created_at')
        read_only_fields = ('id', 'unit_cost', 'line_total', 'created_at')


class WorkshopReturnSerializer(serializers.ModelSerializer):
    contractor_name = serializers.CharField(source='contractor.name', read_only=True, default='')
    from_warehouse_code = serializers.CharField(source='from_warehouse.code', read_only=True, default='')
    to_warehouse_code = serializers.CharField(source='to_warehouse.code', read_only=True, default='')
    issue_no = serializers.CharField(source='issue.issue_no', read_only=True, default='')
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    lines_count = serializers.SerializerMethodField()
    journal_no = serializers.CharField(source='journal.journal_no', read_only=True, default='')

    class Meta:
        model = WorkshopReturn
        fields = ('id', 'return_no', 'return_date', 'issue', 'issue_no',
                  'contractor', 'contractor_name',
                  'from_warehouse', 'from_warehouse_code',
                  'to_warehouse', 'to_warehouse_code',
                  'reason', 'total_qty', 'total_value',
                  'journal', 'journal_no',
                  'status', 'status_display', 'lines_count', 'created_at')
        read_only_fields = ('id', 'total_qty', 'total_value', 'journal',
                            'lines_count', 'created_at')

    def get_lines_count(self, obj):
        return obj.lines.count()


class WorkshopReturnDetailSerializer(WorkshopReturnSerializer):
    lines = WorkshopReturnLineSerializer(many=True, read_only=True)

    class Meta(WorkshopReturnSerializer.Meta):
        fields = WorkshopReturnSerializer.Meta.fields + ('lines',)


class CreateReturnLineInputSerializer(serializers.Serializer):
    issue_line_id = serializers.IntegerField()
    qty = serializers.DecimalField(max_digits=14, decimal_places=3)


class CreateReturnInputSerializer(serializers.Serializer):
    return_no = serializers.CharField(max_length=50)
    return_date = serializers.DateField()
    issue_id = serializers.IntegerField()
    reason = serializers.CharField(required=False, allow_blank=True, default='')
    lines = serializers.ListField(
        child=CreateReturnLineInputSerializer(),
        min_length=1,
    )


# ============================================================================
# PurchaseReturn Serializers
# ============================================================================

class PurchaseReturnLineSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source='product.code', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    lot_no = serializers.CharField(source='lot.batch_no', read_only=True)

    class Meta:
        model = PurchaseReturnLine
        fields = ('id', 'return_doc', 'purchase_line', 'purchase_line_id',
                  'product', 'product_code', 'product_name',
                  'lot', 'lot_no', 'qty', 'unit_price', 'line_total',
                  'created_at')
        read_only_fields = ('id', 'line_total', 'created_at')


class PurchaseReturnSerializer(serializers.ModelSerializer):
    contractor_name = serializers.CharField(source='contractor.name', read_only=True, default='')
    purchase_no = serializers.CharField(source='purchase.purchase_no', read_only=True, default='')
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True, default='')
    cash_account_code = serializers.CharField(source='cash_account.code', read_only=True, default='')
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    lines_count = serializers.SerializerMethodField()
    journal_no = serializers.CharField(source='journal.journal_no', read_only=True, default='')

    class Meta:
        model = PurchaseReturn
        fields = ('id', 'return_no', 'return_date', 'purchase', 'purchase_no',
                  'contractor', 'contractor_name', 'warehouse', 'warehouse_name',
                  'cash_account', 'cash_account_code',
                  'total_qty', 'total_amount', 'reason', 'journal', 'journal_no',
                  'status', 'status_display', 'lines_count', 'created_at')
        read_only_fields = ('id', 'total_qty', 'total_amount', 'journal', 'created_at')

    def get_lines_count(self, obj):
        return obj.lines.count()


class PurchaseReturnDetailSerializer(PurchaseReturnSerializer):
    lines = PurchaseReturnLineSerializer(many=True, read_only=True)

    class Meta(PurchaseReturnSerializer.Meta):
        fields = PurchaseReturnSerializer.Meta.fields + ('lines',)


class CreatePurchaseReturnLineInputSerializer(serializers.Serializer):
    purchase_line_id = serializers.IntegerField()
    qty = serializers.DecimalField(max_digits=14, decimal_places=3)

    def validate_qty(self, value):
        if value <= 0:
            raise serializers.ValidationError('مقدار برگشتی باید بیشتر از صفر باشد.')
        return value


class CreatePurchaseReturnInputSerializer(serializers.Serializer):
    return_no = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    return_date = serializers.DateField()
    purchase_id = serializers.IntegerField()
    reason = serializers.CharField(required=False, allow_blank=True, default='')
    lines = serializers.ListField(
        child=CreatePurchaseReturnLineInputSerializer(),
        min_length=1,
    )
