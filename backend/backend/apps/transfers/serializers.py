"""
Transfers Serializers
"""
from rest_framework import serializers
from .models import TransferHeader, TransferLine, TransferSuggestion


class TransferLineSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source='product.code', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    lot_batch_no = serializers.CharField(source='lot.batch_no', read_only=True)

    class Meta:
        model = TransferLine
        fields = ('id', 'transfer', 'product', 'product_code', 'product_name',
                  'lot', 'lot_batch_no', 'qty', 'expiry_date')
        read_only_fields = ('id', 'transfer', 'expiry_date')


class TransferHeaderSerializer(serializers.ModelSerializer):
    from_store_name = serializers.CharField(source='from_store.name', read_only=True)
    from_store_code = serializers.CharField(source='from_store.code', read_only=True)
    to_store_name = serializers.CharField(source='to_store.name', read_only=True)
    to_store_code = serializers.CharField(source='to_store.code', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    lines_count = serializers.SerializerMethodField()

    class Meta:
        model = TransferHeader
        fields = ('id', 'transfer_no', 'from_store', 'from_store_name', 'from_store_code',
                  'to_store', 'to_store_name', 'to_store_code', 'transfer_date',
                  'status', 'status_display', 'initiator', 'receiver', 'reason',
                  'journal', 'notes', 'lines_count', 'created_at')
        read_only_fields = ('id', 'transfer_no', 'initiator', 'receiver',
                          'journal', 'created_at')

    def get_lines_count(self, obj):
        return obj.lines.count()


class TransferDetailSerializer(TransferHeaderSerializer):
    lines = TransferLineSerializer(many=True, read_only=True)

    class Meta(TransferHeaderSerializer.Meta):
        fields = TransferHeaderSerializer.Meta.fields + ('lines',)


class CreateTransferInputSerializer(serializers.Serializer):
    from_store_id = serializers.IntegerField()
    to_store_id = serializers.IntegerField()
    transfer_date = serializers.DateField(required=False)
    reason = serializers.CharField(required=False, allow_blank=True)
    lines = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
    )


class TransferSuggestionSerializer(serializers.ModelSerializer):
    lot_batch_no = serializers.CharField(source='lot.batch_no', read_only=True)
    product_code = serializers.CharField(source='lot.product.code', read_only=True)
    product_name = serializers.CharField(source='lot.product.name', read_only=True)
    from_store_name = serializers.CharField(source='from_store.name', read_only=True)
    to_store_name = serializers.CharField(source='to_store.name', read_only=True)
    urgency_display = serializers.CharField(source='get_urgency_display', read_only=True)
    days_to_expiry = serializers.SerializerMethodField()

    class Meta:
        model = TransferSuggestion
        fields = ('id', 'lot', 'lot_batch_no', 'product_code', 'product_name',
                  'from_store', 'from_store_name', 'to_store', 'to_store_name',
                  'qty', 'urgency', 'urgency_display', 'score', 'is_approved',
                  'is_processed', 'days_to_expiry', 'created_at', 'processed_at', 'notes')
        read_only_fields = ('id', 'score', 'is_approved', 'is_processed',
                          'processed_at', 'created_at')

    def get_days_to_expiry(self, obj):
        return obj.days_to_expiry
