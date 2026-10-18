"""
Approval Workflow Views
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core.permissions import IsManager
from .models import ApprovalQueue, ApprovalRule
from .serializers import (
    ApprovalQueueSerializer, ApprovalDecisionInputSerializer,
    ApprovalRuleSerializer,
)
from .services import ApprovalService


class ApprovalQueueViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet برای صف تأیید"""
    queryset = ApprovalQueue.objects.all()
    serializer_class = ApprovalQueueSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['ref_doc_type', 'status', 'priority', 'assigned_to',
                        'requested_by']
    search_fields = ['notes', 'decision_reason']
    ordering = ['-priority', '-requested_at']

    def get_queryset(self):
        qs = super().get_queryset()
        # مدیر همه را می‌بیند
        if self.request.user.role == 'manager':
            return qs
        # سایر کاربران فقط درخواست‌های خودشان را می‌بینند
        return qs.filter(requested_by=self.request.user)

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """لیست آیتم‌های در انتظار"""
        qs = ApprovalService.get_pending_list(
            user_id=request.user.id if request.user.role == 'manager' else None,
            doc_type=request.query_params.get('doc_type'),
        )
        # فیلتر کاربر غیر مدیر
        if request.user.role != 'manager':
            qs = qs.filter(requested_by=request.user)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def pending_count(self, request):
        """تعداد آیتم‌های در انتظار"""
        count = ApprovalService.get_pending_count(
            user_id=request.user.id if request.user.role == 'manager' else None,
        )
        return Response({'count': count})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsManager])
    def decide(self, request, pk=None):
        """تأیید یا رد یک آیتم"""
        serializer = ApprovalDecisionInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            if data['decision'] == 'approved':
                result = ApprovalService.approve(
                    approval_id=int(pk),
                    approved_by_id=request.user.id,
                    reason=data.get('reason', ''),
                    notes=data.get('notes', ''),
                )
                return Response({
                    'status': 'approved',
                    'approval': ApprovalQueueSerializer(
                        result['approval'], context={'request': request}
                    ).data,
                    'posted_doc_id': result.get('posted_doc'),
                })
            else:
                approval = ApprovalService.reject(
                    approval_id=int(pk),
                    rejected_by_id=request.user.id,
                    reason=data.get('reason', 'بدون دلیل'),
                )
                return Response({
                    'status': 'rejected',
                    'approval': ApprovalQueueSerializer(
                        approval, context={'request': request}
                    ).data,
                })
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ApprovalRuleViewSet(viewsets.ModelViewSet):
    """ViewSet برای قوانین تأیید خودکار"""
    queryset = ApprovalRule.objects.all()
    serializer_class = ApprovalRuleSerializer
    permission_classes = [IsAuthenticated, IsManager]
    filterset_fields = ['doc_type', 'is_active']
    ordering = ['doc_type']
