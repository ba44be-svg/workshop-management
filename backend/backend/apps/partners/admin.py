"""
Partners Admin
"""
from django.contrib import admin
from .models import Distributor, Store, Customer, PartnerCredit, LoyaltyPoint


@admin.register(Distributor)
class DistributorAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'mobile', 'commission_rate', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('code', 'name', 'mobile')
    ordering = ('code',)


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'distributor', 'tier', 'sales_model',
                    'credit_limit', 'current_credit', 'loyalty_points', 'is_active')
    list_filter = ('tier', 'sales_model', 'is_active', 'distributor')
    search_fields = ('code', 'name', 'address', 'phone')
    ordering = ('code',)
    readonly_fields = ('current_credit', 'loyalty_points')


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'platform', 'phone', 'credit_limit', 'is_active')
    list_filter = ('type', 'platform', 'is_active')
    search_fields = ('name', 'phone', 'platform_user_id')


@admin.register(PartnerCredit)
class PartnerCreditAdmin(admin.ModelAdmin):
    list_display = ('store', 'total_purchases', 'total_paid', 'total_returns',
                    'balance', 'last_transaction')
    list_filter = ('last_transaction',)
    search_fields = ('store__name', 'store__code')
    readonly_fields = ('last_transaction',)


@admin.register(LoyaltyPoint)
class LoyaltyPointAdmin(admin.ModelAdmin):
    list_display = ('store', 'points_change', 'reason', 'new_balance', 'created_at')
    list_filter = ('reason', 'created_at')
    search_fields = ('store__name',)
    readonly_fields = ('new_balance', 'created_at')
    date_hierarchy = 'created_at'
