"""
Accounting Admin
"""
from django.contrib import admin
from .models import (
    Account, CostCenter, FiscalPeriod, JournalTemplate,
    JournalHeader, JournalLine, ExchangeRate,
)


class JournalLineInline(admin.TabularInline):
    model = JournalLine
    extra = 2
    fields = ('account', 'cost_center', 'debit', 'credit', 'description')


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'type', 'parent', 'is_active', 'is_postable')
    list_filter = ('type', 'is_active', 'is_postable')
    search_fields = ('code', 'name')
    ordering = ('code',)


@admin.register(CostCenter)
class CostCenterAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'parent', 'type', 'is_active')
    list_filter = ('type', 'is_active')
    search_fields = ('code', 'name')
    ordering = ('code',)


@admin.register(FiscalPeriod)
class FiscalPeriodAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'start_date', 'end_date', 'is_closed')
    list_filter = ('type', 'is_closed')
    search_fields = ('name',)
    ordering = ('-start_date',)


@admin.register(JournalTemplate)
class JournalTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'source_type', 'is_active')
    list_filter = ('source_type', 'is_active')
    search_fields = ('name',)


@admin.register(JournalHeader)
class JournalHeaderAdmin(admin.ModelAdmin):
    list_display = ('journal_no', 'date', 'source_type', 'total_debit',
                    'total_credit', 'status', 'is_balanced')
    list_filter = ('status', 'source_type', 'date')
    search_fields = ('journal_no', 'description')
    date_hierarchy = 'date'
    ordering = ('-date',)
    inlines = [JournalLineInline]
    readonly_fields = ('total_debit', 'total_credit')


@admin.register(JournalLine)
class JournalLineAdmin(admin.ModelAdmin):
    list_display = ('journal', 'account', 'debit', 'credit', 'description')
    list_filter = ('account__type',)
    search_fields = ('journal__journal_no', 'account__code')


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ('currency', 'rate', 'effective_date')
    list_filter = ('currency',)
    date_hierarchy = 'effective_date'
