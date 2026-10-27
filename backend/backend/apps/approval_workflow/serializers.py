"""
Approval Workflow Serializers
"""
from rest_framework import serializers
from .models import ApprovalQueue, ApprovalRule


class ApprovalQueueSerializer(serializers.ModelSerializer):
    requested_by_username = serializers.CharField(
        source='requested_by.username', read_only=True, default=''
    )
    assigned_to_username = serializers.CharField(
        source='assigned_to.username', read_only=True, default=''
    )
    decided_by_username = serializers.CharField(
        source='decided_by.username', read_only=True, default=''
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    ref_doc_type_display = serializers.CharField(
        source='get_ref_doc_type_display', read_only=True
    )

    class Meta:
        model = ApprovalQueue
        fields = ('id', 'ref_doc_type', 'ref_doc_type_display', 'ref_doc_id',
                  'requested_by', 'requested_by_username', 'requested_at',
                  'assigned_to', 'assigned_to_username',
                  'status', 'status_display', 'priority', 'priority_display',
                  'decision_reason', 'decided_at', 'decided_by', 'decided_by_username',
                  'notes', 'created_at')
        read_only_fields = ('id', 'requested_at', 'decided_at', 'created_at')


class ApprovalDecisionInputSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=['approved', 'rejected'])
    reason = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)


class ApprovalRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalRule
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')
