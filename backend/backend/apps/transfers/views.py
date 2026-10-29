"""
Transfers Views
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core.permissions import IsManager, IsManagerOrStorekeeper
from .models import TransferHeader, TransferLine, TransferSuggestion
from .serializers import (
    TransferHeaderSerializer, TransferDetailSerializer,
    TransferLineSerializer, TransferSuggestionSerializer,
    CreateTransferInputSerializer,
)
from .services import TransferService, TransferSuggesterService


class TransferHeaderViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet برای مشاهده انتقال‌ها"""
    queryset = TransferHeader.objects.filter(deleted_at__isnull=True)
    permission_classes = [IsAuthenticated]
    filterset_fields = ['from_store', 'to_store', 'status', 'transfer_date']
    search_fields = ['transfer_no', 'reason', 'notes']
    ordering = ['-transfer_date', '-id']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TransferDetailSerializer
        return TransferHeaderSerializer

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsManagerOrStorekeeper])
    def create_transfer(self, request):
        """ساخت درخواست انتقال"""
        serializer = CreateTransferInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            transfer = TransferService.create_transfer(
                from_store_id=serializer.validated_data['from_store_id'],
                to_store_id=serializer.validated_data['to_store_id'],
                lines=serializer.validated_data['lines'],
                reason=serializer.validated_data.get('reason', ''),
                transfer_date=serializer.validated_data.get('transfer_date'),
                created_by=request.user,
            )
            return Response(
                TransferDetailSerializer(transfer, context={'request': request}).data,
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsManager])
    def approve(self, request, pk=None):
        """تأیید انتقال توسط مدیر"""
        try:
            transfer = TransferService.approve_transfer(
                transfer_id=int(pk), approved_by=request.user,
            )
            return Response(TransferDetailSerializer(
                transfer, context={'request': request}
            ).data)
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsManager])
    def reject(self, request, pk=None):
        """رد انتقال"""
        reason = request.data.get('reason', '')
        try:
            transfer = TransferService.reject_transfer(
                transfer_id=int(pk), reason=reason, rejected_by=request.user,
            )
            return Response(TransferHeaderSerializer(
                transfer, context={'request': request}
            ).data)
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class TransferLineViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TransferLine.objects.all()
    serializer_class = TransferLineSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['transfer', 'product', 'lot']


class TransferSuggestionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet برای پیشنهادهای انتقال FEFO"""

    queryset = TransferSuggestion.objects.all()
    serializer_class = TransferSuggestionSerializer
    permission_classes = [IsAuthenticated, IsManager]
    filterset_fields = ['from_store', 'to_store', 'urgency', 'is_approved', 'is_processed']
    ordering = ['-score', '-urgency', '-created_at']

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """تولید پیشنهادهای جدید (اجرای دستی الگوریتم)"""
        count = TransferSuggesterService.generate_suggestions()
        return Response({
            'message': f'{count} پیشنهاد جدید تولید شد',
            'count': count,
        })

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """تأیید یک پیشنهاد و ساخت انتقال"""
        try:
            transfer = TransferSuggesterService.approve_suggestion(
                suggestion_id=int(pk), approved_by=request.user,
            )
            return Response(
                TransferDetailSerializer(transfer, context={'request': request}).data,
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=['post'])
    def approve_all(self, request):
        """تأیید همه پیشنهادهای پردازش‌نشده"""
        count = TransferSuggesterService.approve_all_pending(
            approved_by=request.user,
        )
        return Response({
            'message': f'{count} پیشنهاد تأیید و تبدیل به انتقال شد',
            'approved_count': count,
        })
