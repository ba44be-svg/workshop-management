"""
Inventory Admin
"""
from django.contrib import admin
from .models import Warehouse, InventoryLot, InventoryMovement, StockBalance


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'type', 'store', 'is_active')
    list_filter = ('type', 'is_active')
    search_fields = ('code', 'name')
    ordering = ('code',)


@admin.register(InventoryLot)
class InventoryLotAdmin(admin.ModelAdmin):
    list_display = ('batch_no', 'product', 'warehouse', 'production_date',
                    'expiry_date', 'current_qty', 'weighted_avg_cost', 'status')
    list_filter = ('status', 'warehouse', 'product__category')
    search_fields = ('batch_no', 'product__code', 'product__name')
    date_hierarchy = 'production_date'
    ordering = ('-expiry_date',)
    readonly_fields = ('weighted_avg_cost',)


@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    list_display = ('lot', 'product', 'warehouse', 'movement_type', 'qty',
                    'unit_cost', 'ref_doc_type', 'created_at')
    list_filter = ('movement_type', 'ref_doc_type', 'created_at')
    search_fields = ('lot__batch_no', 'product__code')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)


@admin.register(StockBalance)
class StockBalanceAdmin(admin.ModelAdmin):
    list_display = ('product', 'warehouse', 'total_qty', 'total_value', 'updated_at')
    list_filter = ('warehouse',)
    search_fields = ('product__code', 'product__name')
    readonly_fields = ('updated_at',)
    ordering = ('-updated_at',)
