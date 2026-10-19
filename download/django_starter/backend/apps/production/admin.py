"""
Production Admin
"""
from django.contrib import admin
from .models import ProductionBatch, ProductionConsumption, ProductionOutput


class ProductionConsumptionInline(admin.TabularInline):
    model = ProductionConsumption
    extra = 1
    fields = ('material_lot', 'qty_consumed', 'cost_at_consumption')
    readonly_fields = ('cost_at_consumption',)


class ProductionOutputInline(admin.TabularInline):
    model = ProductionOutput
    extra = 1
    fields = ('product', 'qty_produced', 'qty_waste', 'lot')
    readonly_fields = ('lot',)


@admin.register(ProductionBatch)
class ProductionBatchAdmin(admin.ModelAdmin):
    list_display = ('batch_no', 'product', 'planned_qty', 'actual_qty',
                    'waste_qty', 'status', 'weighted_avg_cost',
                    'start_at', 'end_at')
    list_filter = ('status', 'product', 'start_at', 'end_at')
    search_fields = ('batch_no', 'product__code', 'product__name')
    date_hierarchy = 'start_at'
    ordering = ('-start_at',)
    readonly_fields = ('actual_qty', 'waste_qty', 'weighted_avg_cost',
                       'start_at', 'end_at')
    inlines = [ProductionConsumptionInline, ProductionOutputInline]


@admin.register(ProductionConsumption)
class ProductionConsumptionAdmin(admin.ModelAdmin):
    list_display = ('batch', 'material_lot', 'qty_consumed',
                    'cost_at_consumption', 'consumed_at')
    list_filter = ('consumed_at',)
    search_fields = ('batch__batch_no', 'material_lot__batch_no')
    readonly_fields = ('cost_at_consumption', 'consumed_at')
    date_hierarchy = 'consumed_at'


@admin.register(ProductionOutput)
class ProductionOutputAdmin(admin.ModelAdmin):
    list_display = ('batch', 'product', 'qty_produced', 'qty_waste',
                    'lot', 'output_at')
    list_filter = ('output_at', 'product')
    search_fields = ('batch__batch_no', 'product__code', 'lot__batch_no')
    readonly_fields = ('lot', 'output_at')
    date_hierarchy = 'output_at'
