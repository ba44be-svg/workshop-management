"""
Saman Tax Serializers
"""
from rest_framework import serializers
from .models import TaxInvoice


class TaxInvoiceSerializer(serializers.ModelSerializer):
    store_name = serializers.CharField(source='store.name', read_only=True)
    sale_no = serializers.CharField(source='sale.sale_no', read_only=True, default='')
    status_display = serializers.CharField(source='get_invoice_status_display', read_only=True)
    is_confirmed = serializers.SerializerMethodField()

    class Meta:
        model = TaxInvoice
        fields = ('id', 'store', 'store_name', 'sale', 'sale_no',
                  'saman_uid', 'invoice_status', 'status_display',
                  'header_data', 'body_data', 'sent_at', 'confirmed_at',
                  'rejection_reason', 'retry_count', 'is_confirmed',
                  'created_at', 'updated_at')
        read_only_fields = ('id', 'saman_uid', 'sent_at', 'confirmed_at',
                          'rejection_reason', 'retry_count', 'created_at', 'updated_at',
                          'invoice_status')

    def get_is_confirmed(self, obj):
        return obj.is_confirmed


class SendInvoiceInputSerializer(serializers.Serializer):
    sale_id = serializers.IntegerField()


class CheckStatusInputSerializer(serializers.Serializer):
    invoice_id = serializers.IntegerField()


class CancelInvoiceInputSerializer(serializers.Serializer):
    invoice_id = serializers.IntegerField()
    reason = serializers.CharField(required=False, allow_blank=True)
