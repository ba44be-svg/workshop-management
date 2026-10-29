"""
Dispatch Admin
"""
from django.contrib import admin
from .models import Vehicle, Route, DispatchHeader, DispatchLine, SalespersonVisit


class DispatchLineInline(admin.TabularInline):
    model = DispatchLine
    extra = 1
    fields = ('product', 'lot', 'qty', 'unit_price', 'dest_store')


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('plate', 'capacity', 'driver_name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('plate', 'driver_name')


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('distributor', 'day_of_week', 'is_active')
    list_filter = ('day_of_week', 'is_active')
    search_fields = ('distributor__name',)


@admin.register(DispatchHeader)
class DispatchHeaderAdmin(admin.ModelAdmin):
    list_display = ('dispatch_no', 'distributor', 'dispatch_date',
                    'total_qty', 'total_amount', 'status', 'vehicle')
    list_filter = ('status', 'dispatch_date', 'distributor')
    search_fields = ('dispatch_no', 'distributor__name')
    date_hierarchy = 'dispatch_date'
    inlines = [DispatchLineInline]


@admin.register(DispatchLine)
class DispatchLineAdmin(admin.ModelAdmin):
    list_display = ('dispatch', 'product', 'lot', 'qty',
                    'unit_price', 'dest_store')
    list_filter = ('dispatch__status', 'dest_store')
    search_fields = ('dispatch__dispatch_no', 'product__code')


@admin.register(SalespersonVisit)
class SalespersonVisitAdmin(admin.ModelAdmin):
    list_display = ('distributor', 'store', 'visit_date',
                    'check_in_time', 'check_out_time', 'sales_count')
    list_filter = ('visit_date',)
    search_fields = ('distributor__name', 'store__name')
    date_hierarchy = 'visit_date'
