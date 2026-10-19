"""
Payments Views
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.http import HttpResponseRedirect, JsonResponse
from core.permissions import IsManager, IsStoreOwner, IsManagerOrAccountant
from .models import PaymentTransaction, CheckPayment, CashReceipt
from .models import PaymentStatus
from .serializers import (
    PaymentTransactionSerializer, InitiatePaymentInputSerializer,
    InitiatePaymentResponseSerializer,
    CheckPaymentSerializer, CashReceiptSerializer,
)
from .services import PaymentService


class PaymentTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet برای تراکنش‌های پرداخت"""
    queryset = PaymentTransaction.objects.all()
    serializer_class = PaymentTransactionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['store', 'gateway', 'status', 'related_doc_type', 'created_at']
    search_fields = ['transaction_no', 'ref_id', 'authority']
    ordering = ['-created_at']

    def get_queryset(self):
        """فروشگاه‌ها فقط تراکنش‌های خودشان را می‌بینند"""
        qs = super().get_queryset()
        if self.request.user.role == 'store_owner':
            qs = qs.filter(store=self.request.user.profile.store)
        return qs

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsStoreOwner])
    def initiate(self, request):
        """شروع پرداخت آنلاین"""
        serializer = InitiatePaymentInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            result = PaymentService.initiate_payment(
                store_id=data['store_id'],
                amount=data['amount'],
                related_doc_type=data['related_doc_type'],
                related_doc_id=data['related_doc_id'],
                gateway=data.get('gateway'),
                description=data.get('description', ''),
                created_by=request.user,
            )
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def history(self, request):
        """تاریخچه پرداخت‌های فروشگاه"""
        store_id = request.query_params.get('store_id')
        status_filter = request.query_params.get('status')

        if not store_id and request.user.role == 'store_owner':
            store_id = request.user.profile.store.id

        if not store_id:
            return Response(
                {'detail': 'store_id لازم است'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        transactions = PaymentService.get_payment_history(int(store_id), status_filter)
        page = self.paginate_queryset(transactions)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(transactions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsManager])
    def refund(self, request, pk=None):
        """بازگشت وجه"""
        try:
            tx = PaymentService.refund_payment(
                transaction_id=int(pk), refunded_by=request.user,
            )
            return Response(PaymentTransactionSerializer(
                tx, context={'request': request}
            ).data)
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


# Callback URLs — قابل دسترسی بدون احراز هویت (درگاه ارسال می‌کند)
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def zarinpal_callback(request):
    """Callback از زرین‌پال"""
    tx_id = request.query_params.get('tx_id') or request.data.get('tx_id')
    authority = request.query_params.get('Authority') or request.data.get('Authority')
    status_str = request.query_params.get('Status') or request.data.get('Status')

    if not tx_id:
        return Response({'detail': 'tx_id missing'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        PaymentService.handle_callback(
            transaction_id=int(tx_id),
            status_str=status_str or 'NOK',
            authority=authority,
        )
        return Response({
            'status': 'processed',
            'transaction_id': tx_id,
        })
    except Exception as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def idpay_callback(request):
    """Callback از آیدی‌پی"""
    tx_id = request.query_params.get('tx_id') or request.data.get('tx_id')
    status_str = request.query_params.get('status') or request.data.get('status', 'NOK')
    authority = request.query_params.get('id') or request.data.get('id')

    if not tx_id:
        return Response({'detail': 'tx_id missing'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        PaymentService.handle_callback(
            transaction_id=int(tx_id),
            status_str=status_str,
            authority=authority,
        )
        return Response({'status': 'processed'})
    except Exception as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def parsian_callback(request):
    """Callback از پارسیان"""
    tx_id = request.query_params.get('tx_id') or request.data.get('tx_id')
    authority = request.query_params.get('Token') or request.data.get('Token')
    status_str = request.query_params.get('status') or request.data.get('status', 'NOK')

    if not tx_id:
        return Response({'detail': 'tx_id missing'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        PaymentService.handle_callback(
            transaction_id=int(tx_id),
            status_str=status_str,
            authority=authority,
        )
        return Response({'status': 'processed'})
    except Exception as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CheckPaymentViewSet(viewsets.ModelViewSet):
    """ViewSet برای چک‌ها"""
    queryset = CheckPayment.objects.all()
    serializer_class = CheckPaymentSerializer
    permission_classes = [IsAuthenticated, IsManagerOrAccountant]
    filterset_fields = ['store', 'is_cashed', 'due_date']
    search_fields = ['check_number', 'bank_name', 'store__name']
    ordering = ['-due_date']

    @action(detail=True, methods=['post'])
    def cash(self, request, pk=None):
        """وصول چک"""
        check = self.get_object()
        check.is_cashed = True
        check.cashed_at = timezone.now().date()
        check.save(update_fields=['is_cashed', 'cashed_at'])
        return Response(CheckPaymentSerializer(
            check, context={'request': request}
        ).data)


class CashReceiptViewSet(viewsets.ModelViewSet):
    """ViewSet برای رسیدهای نقدی"""
    queryset = CashReceipt.objects.all()
    serializer_class = CashReceiptSerializer
    permission_classes = [IsAuthenticated, IsManagerOrAccountant]
    filterset_fields = ['store', 'received_by', 'receipt_date']
    search_fields = ['receipt_no', 'received_from']
    ordering = ['-receipt_date']


from django.utils import timezone  # noqa
