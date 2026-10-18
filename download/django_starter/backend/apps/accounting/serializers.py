"""
Accounting Serializers
"""
from rest_framework import serializers
from .models import (
    Account, CostCenter, FiscalPeriod, JournalTemplate,
    JournalHeader, JournalLine, ExchangeRate,
)


class AccountSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    parent_code = serializers.CharField(source='parent.code', read_only=True, default='')
    balance = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = ('id', 'code', 'name', 'type', 'type_display', 'parent',
                  'parent_code', 'is_active', 'is_postable', 'description',
                  'balance', 'created_at')
        read_only_fields = ('id', 'balance', 'created_at')

    def get_balance(self, obj):
        # در context اگر as_of_date داده شده باشه، استفاده می‌شه
        as_of = self.context.get('as_of_date')
        return str(obj.get_balance(as_of))


class CostCenterSerializer(serializers.ModelSerializer):
    parent_code = serializers.CharField(source='parent.code', read_only=True, default='')

    class Meta:
        model = CostCenter
        fields = ('id', 'code', 'name', 'parent', 'parent_code', 'type', 'is_active')
        read_only_fields = ('id',)


class FiscalPeriodSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = FiscalPeriod
        fields = ('id', 'name', 'type', 'type_display', 'start_date',
                  'end_date', 'is_closed', 'closed_at', 'closed_by')
        read_only_fields = ('id', 'closed_at', 'closed_by')


class JournalTemplateSerializer(serializers.ModelSerializer):
    source_type_display = serializers.CharField(source='get_source_type_display', read_only=True)

    class Meta:
        model = JournalTemplate
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class JournalLineSerializer(serializers.ModelSerializer):
    account_code = serializers.CharField(source='account.code', read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)
    cost_center_code = serializers.CharField(source='cost_center.code', read_only=True, default='')

    class Meta:
        model = JournalLine
        fields = ('id', 'journal', 'account', 'account_code', 'account_name',
                  'cost_center', 'cost_center_code', 'debit', 'credit',
                  'description', 'ref_doc_type', 'ref_doc_id', 'created_at')
        read_only_fields = ('id', 'created_at')


class JournalHeaderSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_balanced = serializers.SerializerMethodField()
    lines_count = serializers.SerializerMethodField()

    class Meta:
        model = JournalHeader
        fields = ('id', 'journal_no', 'date', 'source_type', 'source_id',
                  'total_debit', 'total_credit', 'status', 'status_display',
                  'period', 'description', 'is_balanced', 'lines_count',
                  'reversed_by_journal', 'created_at')
        read_only_fields = ('id', 'journal_no', 'total_debit', 'total_credit',
                          'is_balanced', 'created_at')

    def get_is_balanced(self, obj):
        return obj.is_balanced

    def get_lines_count(self, obj):
        return obj.lines.count()


class JournalDetailSerializer(JournalHeaderSerializer):
    lines = JournalLineSerializer(many=True, read_only=True)

    class Meta(JournalHeaderSerializer.Meta):
        fields = JournalHeaderSerializer.Meta.fields + ('lines',)


class CreateJournalInputSerializer(serializers.Serializer):
    """input برای ساخت سند دستی"""
    date = serializers.DateField()
    description = serializers.CharField()
    lines = serializers.ListField(
        child=serializers.DictField(),
        min_length=2,  # حداقل ۲ خط برای سند دوطرفه
    )


class ExchangeRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeRate
        fields = '__all__'
        read_only_fields = ('id', 'created_at')
