"""
Products Serializers
"""
from rest_framework import serializers
from .models import Product, ProductCategory, Unit, PricingRule, ProductImage, Barcode, BarcodeScan


class ProductCategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    products_count = serializers.SerializerMethodField()

    class Meta:
        model = ProductCategory
        fields = ('id', 'code', 'name', 'parent', 'level', 'is_active',
                  'children', 'products_count', 'created_at')
        read_only_fields = ('id', 'level', 'created_at')

    def get_children(self, obj):
        children = obj.children.filter(deleted_at__isnull=True)
        return ProductCategorySerializer(children, many=True).data if children.exists() else []

    def get_products_count(self, obj):
        return obj.products.filter(deleted_at__isnull=True).count()


class UnitSerializer(serializers.ModelSerializer):
    """Serializer برای واحدهای اندازه‌گیری."""

    class Meta:
        model = Unit
        fields = ('id', 'code', 'name', 'is_active', 'created_at')
        read_only_fields = ('id', 'created_at')


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('id', 'product', 'image', 'alt_text', 'is_primary', 'sort_order')
        read_only_fields = ('id',)


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    unit_code = serializers.CharField(source='unit.code', read_only=True)
    unit_name = serializers.CharField(source='unit.name', read_only=True)
    default_image_url = serializers.SerializerMethodField()
    primary_pricing = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ('id', 'code', 'name', 'category', 'category_name',
                  'unit', 'unit_code', 'unit_name', 'is_finished_good',
                  'shelf_life_days', 'default_price', 'cost_center', 'barcode',
                  'description', 'is_active', 'default_image_url', 'primary_pricing',
                  'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_default_image_url(self, obj):
        image = obj.default_image
        if image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(image.image.url)
            return image.image.url
        return None

    def get_primary_pricing(self, obj):
        """قیمت‌گذاری فعلی برای لایه عادی"""
        from django.utils import timezone
        pricing = obj.pricing_rules.filter(
            store_tier='regular',
            effective_date__lte=timezone.now().date(),
        ).order_by('-effective_date').first()
        if pricing:
            return {
                'min_price': str(pricing.min_price),
                'default_price': str(pricing.default_price),
            }
        return None

    def validate_code(self, value):
        """کد یکتا"""
        qs = Product.objects.filter(code=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('کد محصول تکراری است')
        return value


class ProductDetailSerializer(ProductSerializer):
    """serializer با جزئیات بیشتر"""
    images = ProductImageSerializer(many=True, read_only=True)
    pricing_rules = serializers.SerializerMethodField()

    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + ('images', 'pricing_rules')

    def get_pricing_rules(self, obj):
        rules = obj.pricing_rules.filter(
            deleted_at__isnull=True,
        ).order_by('store_tier', '-effective_date')
        return PricingRuleSerializer(rules, many=True).data


class PricingRuleSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source='product.code', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = PricingRule
        fields = ('id', 'product', 'product_code', 'product_name', 'store_tier',
                  'min_price', 'default_price', 'effective_date', 'expires_at')
        read_only_fields = ('id',)


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
