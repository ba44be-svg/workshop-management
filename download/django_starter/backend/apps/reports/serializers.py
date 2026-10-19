"""
Reports Serializers
"""
from rest_framework import serializers


class DashboardSummarySerializer(serializers.Serializer):
    """serializer برای داشبورد"""
    def to_representation(self, instance):
        return instance  # dict از service


class GeoHeatmapItemSerializer(serializers.Serializer):
    store_id = serializers.IntegerField()
    name = serializers.CharField()
    lat = serializers.FloatField()
    lng = serializers.FloatField()
    total_sales = serializers.CharField()
    intensity = serializers.CharField()
    tier = serializers.CharField()
    sales_count = serializers.IntegerField()


class WasteReportSerializer(serializers.Serializer):
    def to_representation(self, instance):
        return instance


class TopProductSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    product_code = serializers.CharField()
    product_name = serializers.CharField()
    total_qty = serializers.CharField()
    total_amount = serializers.CharField()


class TopStoreSerializer(serializers.Serializer):
    store_id = serializers.IntegerField()
    store_name = serializers.CharField()
    store_code = serializers.CharField()
    total_amount = serializers.CharField()
    sales_count = serializers.IntegerField()
    tier = serializers.CharField()


class SalesTrendItemSerializer(serializers.Serializer):
    date = serializers.CharField()
    total_amount = serializers.CharField()
    sales_count = serializers.IntegerField()
