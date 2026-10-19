"""
Saman Tax Views
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core.permissions import IsManagerOrAccountant
from .models import TaxInvoice
from .serializers import (
    TaxInvoiceSerializer, SendInvoiceInputSerializer,
    CheckStatusInputSerializer, CancelInvoiceInputSerializer,
)
from .services import SamanService


class TaxInvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet برای صورتحساب‌های سامان"""
    queryset = TaxInvoice.objects.all()
    serializer_class = TaxInvoiceSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['store', 'sale', 'invoice_status', 'created_at']
    search_fields = ['saman_uid']
    ordering = ['-created_at']

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsManagerOrAccountant])
    def send(self, request):
        """ارسال صورتحساب به سامان"""
        serializer = SendInvoiceInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # ساخت صورتحساب برای فروش (اگه قبلاً نباشه)
        try:
            invoice = SamanService.create_invoice_for_sale(
                serializer.validated_data['sale_id']
            )
            # ارسال به سامان
            result = SamanService.send_invoice(invoice.id)
            invoice.refresh_from_db()
            return Response({
                'invoice': TaxInvoiceSerializer(invoice, context={'request': request}).data,
                'send_result': result,
            }, status=status.HTTP_200_OK if result.get('success') else status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsManagerOrAccountant])
    def check_status(self, request):
        """بررسی وضعیت صورتحساب"""
        serializer = CheckStatusInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            result = SamanService.check_status(serializer.validated_data['invoice_id'])
            return Response(result)
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsManagerOrAccountant])
    def cancel(self, request):
        """لغو صورتحساب"""
        serializer = CancelInvoiceInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            invoice = SamanService.cancel_invoice(
                invoice_id=serializer.validated_data['invoice_id'],
                reason=serializer.validated_data.get('reason', ''),
            )
            return Response(TaxInvoiceSerializer(
                invoice, context={'request': request}
            ).data)
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsManagerOrAccountant])
    def retry_failed(self, request):
        """تلاش مجدد برای صورتحساب‌های ناموفق"""
        count = SamanService.retry_failed_invoices()
        return Response({
            'message': f'{count} صورتحساب مجدداً ارسال شد',
            'count': count,
        })
