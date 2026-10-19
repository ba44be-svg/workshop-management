"""
Barcode Admin
"""
from django.contrib import admin
from apps.products.models import Barcode, BarcodeScan


@admin.register(Barcode)
class BarcodeAdmin(admin.ModelAdmin):
    list_display = ('barcode_value', 'entity_type', 'entity_id', 'created_at')
    list_filter = ('entity_type',)
    search_fields = ('barcode_value',)
    readonly_fields = ('created_at',)


@admin.register(BarcodeScan)
class BarcodeScanAdmin(admin.ModelAdmin):
    list_display = ('barcode_value', 'scanned_by', 'scan_context',
                    'ref_doc_type', 'scanned_at', 'device_id')
    list_filter = ('scan_context', 'scanned_at')
    search_fields = ('barcode_value', 'scanned_by__username')
    date_hierarchy = 'scanned_at'
    readonly_fields = ('scanned_at',)
