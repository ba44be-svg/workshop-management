"""
Store Portal Admin
"""
from django.contrib import admin
from .models import StoreOrder, StoreOrderLine, StoreNotification, StoreDashboard


class StoreOrderLineInline(admin.TabularInline):
    model = StoreOrderLine
    extra = 1
    fields = ('product', 'qty', 'unit_price', 'is_smart_suggestion')
    readonly_fields = ('unit_price',)


@admin.register(StoreOrder)
class StoreOrderAdmin(admin.ModelAdmin):
    list_display = ('order_no', 'store', 'order_date', 'status',
                    'payment_status', 'total_amount', 'total_qty')
    list_filter = ('status', 'payment_status', 'order_date', 'store')
    search_fields = ('order_no', 'store__name', 'notes')
    date_hierarchy = 'order_date'
    inlines = [StoreOrderLineInline]


@admin.register(StoreOrderLine)
class StoreOrderLineAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'qty', 'unit_price')
    list_filter = ('is_smart_suggestion',)


@admin.register(StoreNotification)
class StoreNotificationAdmin(admin.ModelAdmin):
    list_display = ('store', 'title', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    date_hierarchy = 'created_at'


@admin.register(StoreDashboard)
class StoreDashboardAdmin(admin.ModelAdmin):
    list_display = ('store', 'total_orders', 'active_orders', 'balance',
                    'loyalty_points', 'unread_notifications', 'updated_at')
    list_filter = ('updated_at',)
    readonly_fields = ('updated_at',)
