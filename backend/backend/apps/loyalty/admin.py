"""
Loyalty Admin
"""
from django.contrib import admin
from .models import LoyaltyTier, DiscountRule, ReorderSuggestion


@admin.register(LoyaltyTier)
class LoyaltyTierAdmin(admin.ModelAdmin):
    list_display = ('name', 'min_points', 'discount_percentage',
                    'credit_increase_percentage', 'is_active')
    list_filter = ('is_active',)
    ordering = ('min_points',)


@admin.register(DiscountRule)
class DiscountRuleAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'discount_percentage', 'applies_to_tier',
                    'starts_at', 'expires_at', 'usage_count', 'usage_limit', 'is_active')
    list_filter = ('is_active', 'applies_to_tier')
    search_fields = ('code', 'name')
    date_hierarchy = 'starts_at'


@admin.register(ReorderSuggestion)
class ReorderSuggestionAdmin(admin.ModelAdmin):
    list_display = ('store', 'product', 'suggested_qty', 'current_stock',
                    'daily_rate', 'days_of_stock', 'confidence_score',
                    'is_processed', 'created_at')
    list_filter = ('is_processed', 'created_at')
    search_fields = ('store__name', 'product__code')
    date_hierarchy = 'created_at'
    readonly_fields = ('confidence_score', 'days_of_stock', 'daily_rate', 'current_stock')
