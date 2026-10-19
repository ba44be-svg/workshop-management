"""
Products Views
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core.permissions import IsManager, IsManagerOrStorekeeper, IsStoreOwner
from .models import Product, ProductCategory, PricingRule, ProductImage, Barcode, BarcodeScan
from .serializers import (
    ProductSerializer, ProductDetailSerializer, ProductCategorySerializer,
    PricingRuleSerializer, ProductImageSerializer, BarcodeSerializer,
    BarcodeScanSerializer,
)
from .services import ProductService
from django.db import models


class ProductCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet برای دسته‌بندی محصولات"""
    queryset = ProductCategory.objects.filter(deleted_at__isnull=True)
    serializer_class = ProductCategorySerializer
    permission_classes = [IsAuthenticated, IsManagerOrStorekeeper]
    filterset_fields = ['parent', 'is_active', 'level']
    search_fields = ['code', 'name']
    ordering_fields = ['code', 'name']

    @action(detail=False, methods=['get'])
    def tree(self, request):
        """دریافت درخت کامل دسته‌بندی‌ها"""
        roots = self.queryset.filter(parent__isnull=True)
        serializer = self.get_serializer(roots, many=True)
        return Response(serializer.data)


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet برای محصولات"""
    queryset = Product.objects.filter(deleted_at__isnull=True)
    permission_classes = [IsAuthenticated]
    filterset_fields = ['category', 'is_active', 'cost_center']
    search_fields = ['code', 'name', 'barcode', 'description']
    ordering_fields = ['code', 'name', 'default_price', 'created_at']
    ordering = ['code']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsManagerOrStorekeeper()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        # استفاده از ProductService برای ساخت محصول
        product = ProductService.create_product(
            **serializer.validated_data,
            created_by=self.request.user,
        )
        # به‌روزرسانی serializer.instance برای پاسخ
        serializer.instance = product

    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_image(self, request, pk=None):
        """آپلود تصویر محصول"""
        product = self.get_object()
        image = request.FILES.get('image')
        if not image:
            return Response(
                {'detail': 'فایل تصویر لازم است'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        is_primary = request.data.get('is_primary', False)
        alt_text = request.data.get('alt_text', '')

        img = ProductService.add_product_image(
            product_id=product.id,
            image=image,
            is_primary=is_primary,
            alt_text=alt_text,
            created_by=request.user,
        )

        return Response(
            ProductImageSerializer(img, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['get'])
    def pricing(self, request, pk=None):
        """دریافت قیمت‌گذاری برای محصول"""
        product = self.get_object()
        pricing = product.pricing_rules.filter(
            deleted_at__isnull=True,
        ).order_by('store_tier', '-effective_date')
        return Response(PricingRuleSerializer(pricing, many=True).data)

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """محصولات کم‌موجودی"""
        # این نیاز به inventory app دارد
        from apps.inventory.models import StockBalance
        low_stock_products = []
        for product in self.queryset.filter(is_active=True):
            total = StockBalance.objects.filter(
                product_id=product.id,
            ).aggregate(total=models.Sum('total_qty'))['total'] or 0
            if total < 10:  # حد آستانه
                low_stock_products.append({
                    'product_id': product.id,
                    'code': product.code,
                    'name': product.name,
                    'total_stock': total,
                })
        return Response({'results': low_stock_products})


class PricingRuleViewSet(viewsets.ModelViewSet):
    """ViewSet برای قیمت‌گذاری"""
    queryset = PricingRule.objects.filter(deleted_at__isnull=True)
    serializer_class = PricingRuleSerializer
    permission_classes = [IsAuthenticated, IsManager]
    filterset_fields = ['product', 'store_tier', 'effective_date']
    ordering = ['-effective_date']


class BarcodeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet فقط خواندنی برای بارکدها"""
    queryset = Barcode.objects.all()
    serializer_class = BarcodeSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['entity_type', 'entity_id']
    lookup_field = 'barcode_value'
    lookup_url_kwarg = 'barcode_value'

    @action(detail=False, methods=['post'])
    def scan(self, request):
        """اسکن بارکد از موبایل"""
        barcode_value = request.data.get('barcode_value')
        store_id = request.data.get('store_id')
        context = request.data.get('context', 'sale_draft')

        if not barcode_value:
            return Response(
                {'detail': 'barcode_value لازم است'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # جستجوی بارکد
        try:
            barcode = Barcode.objects.get(barcode_value=barcode_value)
        except Barcode.DoesNotExist:
            # ثبت اسکن ناموفق
            BarcodeScan.objects.create(
                barcode_value=barcode_value,
                scanned_by=request.user,
                scan_context=context,
                device_id=request.data.get('device_id', ''),
            )
            return Response(
                {'detail': 'بارکد یافت نشد', 'found': False},
                status=status.HTTP_404_NOT_FOUND,
            )

        # ثبت اسکن موفق
        BarcodeScan.objects.create(
            barcode=barcode,
            barcode_value=barcode_value,
            scanned_by=request.user,
            scan_context=context,
            device_id=request.data.get('device_id', ''),
        )

        # اگر بارکد محصول، اطلاعات محصول را برگردان
        if barcode.entity_type == 'product':
            product = Product.objects.get(id=barcode.entity_id)

            # قیمت مناسب برای فروشگاه (در صورت ارسال store_id)
            unit_price = None
            if store_id:
                from apps.partners.models import Store
                store = Store.objects.get(id=store_id)
                pricing = ProductService.get_price_for_store(
                    product_id=product.id,
                    store_tier=store.tier,
                )
                if pricing:
                    unit_price = pricing.default_price
                else:
                    unit_price = product.default_price

            return Response({
                'found': True,
                'product': ProductSerializer(product, context={'request': request}).data,
                'unit_price': str(unit_price) if unit_price else None,
            })

        return Response({
            'found': True,
            'entity_type': barcode.entity_type,
            'entity_id': barcode.entity_id,
        })
