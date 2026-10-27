"""
Loyalty Serializers
"""
from rest_framework import serializers
from .models import LoyaltyTier, DiscountRule, ReorderSuggestion


class LoyaltyTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoyaltyTier
        fields = '__all__'
        read_only_fields = ('id',)


class DiscountRuleSerializer(serializers.ModelSerializer):
    is_valid = serializers.SerializerMethodField()

    class Meta:
        model = DiscountRule
        fields = '__all__'
        read_only_fields = ('id', 'usage_count', 'created_at')

    def get_is_valid(self, obj):
        return obj.is_valid


class ReorderSuggestionSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source='product.code', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    store_name = serializers.CharField(source='store.name', read_only=True)

    class Meta:
        model = ReorderSuggestion
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'processed_at', 'confidence_score',
                          'days_of_stock', 'daily_rate', 'current_stock')


class LoyaltyTransactionSerializer(serializers.ModelSerializer):
    """serializer برای تراکنش‌های وفاداری"""
    store_name = serializers.CharField(source='store.name', read_only=True)

    class Meta:
        from apps.partners.models import LoyaltyPoint
        model = LoyaltyPoint
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'new_balance')
