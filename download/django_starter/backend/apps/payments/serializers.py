"""
Payments Serializers
"""
from rest_framework import serializers
from .models import PaymentTransaction, CheckPayment, CashReceipt


class PaymentTransactionSerializer(serializers.ModelSerializer):
    store_name = serializers.CharField(source='store.name', read_only=True)
    gateway_display = serializers.CharField(source='get_gateway_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = PaymentTransaction
        fields = ('id', 'transaction_no', 'store', 'store_name', 'gateway',
                  'gateway_display', 'amount', 'status', 'status_display',
                  'authority', 'ref_id', 'paid_at', 'related_doc_type',
                  'related_doc_id', 'journal', 'description', 'created_at')
        read_only_fields = ('id', 'transaction_no', 'authority', 'ref_id',
                          'paid_at', 'journal', 'gateway_response', 'created_at',
                          'status')


class InitiatePaymentInputSerializer(serializers.Serializer):
    store_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=18, decimal_places=4)
    related_doc_type = serializers.CharField(max_length=50)
    related_doc_id = serializers.IntegerField()
    gateway = serializers.ChoiceField(
        choices=['zarinpal', 'idpay', 'parsian'],
        required=False, allow_null=True,
    )
    description = serializers.CharField(required=False, allow_blank=True)


class InitiatePaymentResponseSerializer(serializers.Serializer):
    transaction_id = serializers.IntegerField()
    transaction_no = serializers.CharField()
    redirect_url = serializers.CharField()
    gateway = serializers.CharField()
    amount = serializers.CharField()


class CheckPaymentSerializer(serializers.ModelSerializer):
    store_name = serializers.CharField(source='store.name', read_only=True)

    class Meta:
        model = CheckPayment
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class CashReceiptSerializer(serializers.ModelSerializer):
    store_name = serializers.CharField(source='store.name', read_only=True)

    class Meta:
        model = CashReceipt
        fields = '__all__'
        read_only_fields = ('id', 'receipt_no', 'created_at')
