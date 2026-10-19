"""
Approval Workflow Admin
"""
from django.contrib import admin
from .models import ApprovalQueue, ApprovalRule


@admin.register(ApprovalQueue)
class ApprovalQueueAdmin(admin.ModelAdmin):
    list_display = ('ref_doc_type', 'ref_doc_id', 'status', 'priority',
                    'requested_by', 'assigned_to', 'requested_at', 'decided_at')
    list_filter = ('status', 'priority', 'ref_doc_type')
    search_fields = ('ref_doc_type', 'notes', 'decision_reason')
    date_hierarchy = 'requested_at'
    readonly_fields = ('requested_at', 'decided_at')


@admin.register(ApprovalRule)
class ApprovalRuleAdmin(admin.ModelAdmin):
    list_display = ('doc_type', 'auto_assign_to', 'auto_priority', 'is_active')
    list_filter = ('doc_type', 'is_active', 'auto_priority')
