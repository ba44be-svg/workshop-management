"""
Saman Tax Admin
"""
from django.contrib import admin
from .models import TaxInvoice


@admin.register(TaxInvoice)
class TaxInvoiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'store', 'sale', 'saman_uid', 'invoice_status',
                    'sent_at', 'confirmed_at', 'retry_count', 'created_at')
    list_filter = ('invoice_status', 'created_at', 'store')
    search_fields = ('saman_uid', 'store__name', 'sale__sale_no')
    date_hierarchy = 'created_at'
    readonly_fields = ('saman_uid', 'sent_at', 'confirmed_at',
                      'retry_count', 'created_at', 'updated_at')
