"""
Workshop Admin
"""
from django.contrib import admin
from .models import (
    Contractor, Employee, PurchaseHeader, PurchaseLine,
    WorkshopIssue, WorkshopIssueLine,
    WorkshopReturn, WorkshopReturnLine,
)


class PurchaseLineInline(admin.TabularInline):
    model = PurchaseLine
    extra = 2
    fields = ('product', 'qty', 'unit_price', 'unit_cost',
              'shelf_life_days', 'expiry_date', 'lot_no', 'line_total')
    readonly_fields = ('unit_cost', 'lot_no', 'line_total')


class WorkshopIssueLineInline(admin.TabularInline):
    model = WorkshopIssueLine
    extra = 2
    fields = ('product', 'lot', 'qty', 'unit_cost', 'line_total')
    readonly_fields = ('unit_cost', 'line_total')


class WorkshopReturnLineInline(admin.TabularInline):
    model = WorkshopReturnLine
    extra = 2
    fields = ('issue_line', 'qty', 'unit_cost', 'line_total')
    readonly_fields = ('unit_cost', 'line_total')


@admin.register(Contractor)
class ContractorAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'mobile', 'workshop_name',
                    'is_active', 'detail_account')
    list_filter = ('is_active',)
    search_fields = ('code', 'name', 'mobile', 'national_id')
    ordering = ('code',)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('code', 'full_name', 'position', 'mobile', 'workshop',
                    'hire_date', 'is_active')
    list_filter = ('is_active', 'position', 'workshop')
    search_fields = ('code', 'first_name', 'last_name', 'national_id',
                     'mobile', 'phone', 'position')
    ordering = ('code',)
    list_editable = ('is_active',)


@admin.register(PurchaseHeader)
class PurchaseHeaderAdmin(admin.ModelAdmin):
    list_display = ('purchase_no', 'purchase_date', 'contractor', 'warehouse',
                    'total_amount', 'total_qty', 'status', 'journal')
    list_filter = ('status', 'purchase_date', 'contractor')
    search_fields = ('purchase_no', 'notes', 'contractor__code', 'contractor__name')
    date_hierarchy = 'purchase_date'
    inlines = [PurchaseLineInline]
    readonly_fields = ('total_amount', 'total_qty', 'journal')


@admin.register(WorkshopIssue)
class WorkshopIssueAdmin(admin.ModelAdmin):
    list_display = ('issue_no', 'issue_date', 'contractor', 'from_warehouse',
                    'to_warehouse', 'total_qty', 'total_value', 'status', 'journal')
    list_filter = ('status', 'issue_date', 'contractor')
    search_fields = ('issue_no', 'notes', 'contractor__code', 'contractor__name')
    date_hierarchy = 'issue_date'
    inlines = [WorkshopIssueLineInline]
    readonly_fields = ('total_qty', 'total_value', 'journal')


@admin.register(WorkshopReturn)
class WorkshopReturnAdmin(admin.ModelAdmin):
    list_display = ('return_no', 'return_date', 'issue', 'contractor',
                    'total_qty', 'total_value', 'status', 'journal')
    list_filter = ('status', 'return_date', 'contractor')
    search_fields = ('return_no', 'reason', 'contractor__code')
    date_hierarchy = 'return_date'
    inlines = [WorkshopReturnLineInline]
    readonly_fields = ('total_qty', 'total_value', 'journal')
