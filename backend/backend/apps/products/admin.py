"""
Products Admin
"""
from django.contrib import admin
from .models import (
    Product, ProductCategory, Unit, PricingRule, ProductImage, Barcode, BarcodeScan
)


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'parent', 'level', 'is_active')
    list_filter = ('level', 'is_active')
    search_fields = ('code', 'name')
    ordering = ('code',)


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('code', 'name')
    ordering = ('code',)
    list_editable = ('is_active',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'category', 'unit', 'is_finished_good',
                    'shelf_life_days', 'default_price', 'barcode', 'is_active')
    list_filter = ('category', 'is_active', 'is_finished_good', 'cost_center')
    search_fields = ('code', 'name', 'barcode', 'description')
    ordering = ('code',)
    readonly_fields = ('created_at', 'updated_at')


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text', 'is_primary', 'sort_order')


@admin.register(PricingRule)
class PricingRuleAdmin(admin.ModelAdmin):
    list_display = ('product', 'store_tier', 'min_price', 'default_price',
                    'effective_date', 'expires_at')
    list_filter = ('store_tier', 'effective_date')
    search_fields = ('product__code', 'product__name')
    date_hierarchy = 'effective_date'


@admin.register(Barcode)
class BarcodeAdmin(admin.ModelAdmin):
    list_display = ('barcode_value', 'entity_type', 'entity_id', 'created_at')
    list_filter = ('entity_type',)
    search_fields = ('barcode_value',)
    readonly_fields = ('created_at',)


@admin.register(BarcodeScan)
class BarcodeScanAdmin(admin.ModelAdmin):
    list_display = ('barcode_value', 'scanned_by', 'scan_context', 'scanned_at', 'device_id')
    list_filter = ('scan_context', 'scanned_at')
    search_fields = ('barcode_value', 'scanned_by__username')
    readonly_fields = ('scanned_at',)
    date_hierarchy = 'scanned_at'
