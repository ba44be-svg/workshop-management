"""
Payments Admin
"""
from django.contrib import admin
from .models import PaymentTransaction, CheckPayment, CashReceipt


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_no', 'store', 'gateway', 'amount', 'status',
                    'ref_id', 'paid_at', 'created_at')
    list_filter = ('gateway', 'status', 'created_at', 'store')
    search_fields = ('transaction_no', 'ref_id', 'authority')
    date_hierarchy = 'created_at'
    readonly_fields = ('transaction_no', 'authority', 'ref_id', 'paid_at',
                      'gateway_response', 'created_at')


@admin.register(CheckPayment)
class CheckPaymentAdmin(admin.ModelAdmin):
    list_display = ('store', 'amount', 'check_number', 'bank_name',
                    'issue_date', 'due_date', 'is_cashed')
    list_filter = ('is_cashed', 'due_date', 'bank_name')
    search_fields = ('check_number', 'bank_name', 'store__name')
    date_hierarchy = 'due_date'


@admin.register(CashReceipt)
class CashReceiptAdmin(admin.ModelAdmin):
    list_display = ('receipt_no', 'store', 'amount', 'received_from',
                    'receipt_date', 'received_by')
    list_filter = ('receipt_date',)
    search_fields = ('receipt_no', 'received_from', 'store__name')
    date_hierarchy = 'receipt_date'
