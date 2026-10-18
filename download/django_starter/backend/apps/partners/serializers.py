"""
Partners Serializers
"""
from rest_framework import serializers
from .models import Distributor, Store, Customer, PartnerCredit, LoyaltyPoint


class DistributorSerializer(serializers.ModelSerializer):
    sales_count = serializers.SerializerMethodField()

    class Meta:
        model = Distributor
        fields = ('id', 'code', 'name', 'mobile', 'vehicle', 'default_route',
                  'commission_rate', 'is_active', 'sales_count', 'created_at')
        read_only_fields = ('id', 'created_at')

    def get_sales_count(self, obj):
        return obj.stores.count()


class StoreSerializer(serializers.ModelSerializer):
    distributor_name = serializers.CharField(source='distributor.name', read_only=True, default='')
    available_credit = serializers.SerializerMethodField()
    discount_percentage = serializers.SerializerMethodField()
    tier_display = serializers.CharField(source='get_tier_display', read_only=True)
    sales_model_display = serializers.CharField(source='get_sales_model_display', read_only=True)

    class Meta:
        model = Store
        fields = ('id', 'code', 'name', 'address', 'phone', 'geo_lat', 'geo_lng',
                  'distributor', 'distributor_name', 'sales_model', 'sales_model_display',
                  'tier', 'tier_display', 'credit_limit', 'current_credit',
                  'available_credit', 'discount_percentage', 'loyalty_points',
                  'is_active', 'created_at')
        read_only_fields = ('id', 'available_credit', 'discount_percentage',
                          'loyalty_points', 'created_at')

    def get_available_credit(self, obj):
        return str(obj.available_credit)

    def get_discount_percentage(self, obj):
        return obj.discount_percentage


class CustomerSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = Customer
        fields = ('id', 'type', 'type_display', 'name', 'phone', 'platform',
                  'platform_user_id', 'credit_limit', 'is_active', 'created_at')
        read_only_fields = ('id', 'created_at')


class PartnerCreditSerializer(serializers.ModelSerializer):
    store_name = serializers.CharField(source='store.name', read_only=True)
    store_code = serializers.CharField(source='store.code', read_only=True)

    class Meta:
        model = PartnerCredit
        fields = '__all__'
        read_only_fields = ('id', 'last_transaction')


class LoyaltyPointSerializer(serializers.ModelSerializer):
    store_name = serializers.CharField(source='store.name', read_only=True)

    class Meta:
        model = LoyaltyPoint
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'new_balance')
