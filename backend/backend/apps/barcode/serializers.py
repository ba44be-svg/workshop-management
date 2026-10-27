"""
Barcode Serializers
"""
from rest_framework import serializers
from apps.products.models import Barcode, BarcodeScan


class BarcodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Barcode
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class BarcodeScanSerializer(serializers.ModelSerializer):
    class Meta:
        model = BarcodeScan
        fields = '__all__'
        read_only_fields = ('id', 'scanned_at')


class ScanInputSerializer(serializers.Serializer):
    barcode_value = serializers.CharField(max_length=50)
    context = serializers.CharField(max_length=50, required=False, default='sale_draft')
    ref_doc_type = serializers.CharField(max_length=50, required=False, allow_blank=True)
    ref_doc_id = serializers.IntegerField(required=False, allow_null=True)
    device_id = serializers.CharField(max_length=100, required=False, allow_blank=True)


class GenerateBarcodeInputSerializer(serializers.Serializer):
    entity_type = serializers.ChoiceField(
        choices=['product', 'lot', 'sales_order', 'store_order', 'dispatch'],
    )
    entity_id = serializers.IntegerField()
    extra_data = serializers.JSONField(required=False)
