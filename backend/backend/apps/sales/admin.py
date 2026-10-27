"""
Sales Admin
"""
from django.contrib import admin
from .models import SalesHeader, SalesLine, ReturnHeader, ReturnLine


class SalesLineInline(admin.TabularInline):
    model = SalesLine
    extra = 1
    fields = ('product', 'lot', 'qty', 'unit_price', 'unit_cost')
    readonly_fields = ('unit_cost',)


@admin.register(SalesHeader)
class SalesHeaderAdmin(admin.ModelAdmin):
    list_display = ('sale_no', 'store', 'sale_date', 'sales_type',
                    'total_amount', 'total_cost', 'status', 'distributor')
    list_filter = ('sales_type', 'status', 'sale_date')
    search_fields = ('sale_no', 'store__name', 'notes')
    date_hierarchy = 'sale_date'
    ordering = ('-sale_date',)
    readonly_fields = ('total_amount', 'total_cost')
    inlines = [SalesLineInline]


@admin.register(SalesLine)
class SalesLineAdmin(admin.ModelAdmin):
    list_display = ('sale', 'product', 'lot', 'qty', 'unit_price', 'unit_cost')
    list_filter = ('sale__sales_type',)
    search_fields = ('sale__sale_no', 'product__code')
    readonly_fields = ('unit_cost',)


class ReturnLineInline(admin.TabularInline):
    model = ReturnLine
    extra = 1
    fields = ('product', 'lot', 'qty', 'condition', 'notes')


@admin.register(ReturnHeader)
class ReturnHeaderAdmin(admin.ModelAdmin):
    list_display = ('return_no', 'store', 'return_date', 'total_qty',
                    'status', 'original_sale')
    list_filter = ('status', 'return_date')
    search_fields = ('return_no', 'store__name', 'reason')
    date_hierarchy = 'return_date'
    inlines = [ReturnLineInline]


@admin.register(ReturnLine)
class ReturnLineAdmin(admin.ModelAdmin):
    list_display = ('return_header', 'product', 'lot', 'qty', 'condition')
    list_filter = ('condition',)
    search_fields = ('return_header__return_no', 'product__code')
