"""
Barcode Views
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core.permissions import IsManager, IsDistributor
from apps.products.models import Barcode, BarcodeScan
from .serializers import (
    BarcodeSerializer, BarcodeScanSerializer,
    ScanInputSerializer, GenerateBarcodeInputSerializer,
)
from .services import BarcodeService


class BarcodeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet برای بارکدها"""
    queryset = Barcode.objects.all()
    serializer_class = BarcodeSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['entity_type', 'entity_id']
    lookup_field = 'barcode_value'
    lookup_url_kwarg = 'barcode_value'

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsManager])
    def generate(self, request):
        """تولید بارکد برای یک موجودیت"""
        serializer = GenerateBarcodeInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        barcode = BarcodeService.create_or_get_barcode(
            entity_type=data['entity_type'],
            entity_id=data['entity_id'],
            created_by=request.user,
            extra_data=data.get('extra_data'),
        )
        return Response(
            BarcodeSerializer(barcode, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def scan(self, request):
        """اسکن بارکد از موبایل"""
        serializer = ScanInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        result = BarcodeService.scan(
            barcode_value=data['barcode_value'],
            scanned_by_id=request.user.id,
            context=data.get('context', 'sale_draft'),
            ref_doc_type=data.get('ref_doc_type', ''),
            ref_doc_id=data.get('ref_doc_id'),
            device_id=data.get('device_id', ''),
        )
        return Response(result)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def image(self, request, barcode_value=None):
        """دریافت تصویر بارکد به‌صورت base64"""
        image_b64 = BarcodeService.get_barcode_image_base64(barcode_value)
        if image_b64:
            return Response({
                'barcode_value': barcode_value,
                'image_base64': image_b64,
                'format': 'svg',
            })
        return Response(
            {'detail': 'Failed to generate barcode image'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def qr_image(self, request, barcode_value=None):
        """دریافت تصویر QR Code"""
        try:
            barcode = Barcode.objects.get(barcode_value=barcode_value)
            image_b64 = BarcodeService.get_qr_image_base64(barcode.qr_code_data)
            if image_b64:
                return Response({
                    'qr_data': barcode.qr_code_data,
                    'image_base64': image_b64,
                    'format': 'png',
                })
        except Barcode.DoesNotExist:
            return Response(
                {'detail': 'Barcode not found'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            {'detail': 'Failed to generate QR image'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class BarcodeScanViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet برای لاگ اسکن‌ها"""
    queryset = BarcodeScan.objects.all()
    serializer_class = BarcodeScanSerializer
    permission_classes = [IsAuthenticated, IsManager]
    filterset_fields = ['scanned_by', 'scan_context', 'barcode']
    ordering = ['-scanned_at']
