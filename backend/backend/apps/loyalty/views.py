"""
Loyalty Views
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core.permissions import IsManager, IsStoreOwner
from .models import LoyaltyTier, DiscountRule, ReorderSuggestion
from .serializers import (
    LoyaltyTierSerializer, DiscountRuleSerializer,
    ReorderSuggestionSerializer, LoyaltyTransactionSerializer,
)
from .services import LoyaltyService, SmartReorderService


class LoyaltyTierViewSet(viewsets.ModelViewSet):
    queryset = LoyaltyTier.objects.all()
    serializer_class = LoyaltyTierSerializer
    permission_classes = [IsAuthenticated, IsManager]
    ordering = ['min_points']


class DiscountRuleViewSet(viewsets.ModelViewSet):
    queryset = DiscountRule.objects.all()
    serializer_class = DiscountRuleSerializer
    permission_classes = [IsAuthenticated, IsManager]
    filterset_fields = ['applies_to_tier', 'is_active']
    ordering = ['-starts_at']


class ReorderSuggestionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet برای پیشنهادهای Smart Reorder"""
    queryset = ReorderSuggestion.objects.all()
    serializer_class = ReorderSuggestionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['store', 'product', 'is_processed']
    ordering = ['days_of_stock']

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.role == 'store_owner':
            qs = qs.filter(store=self.request.user.profile.store)
        return qs

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsStoreOwner])
    def generate(self, request):
        """تولید پیشنهاد برای فروشگاه فعلی"""
        store = request.user.profile.store
        suggestions = SmartReorderService.generate_suggestions(store_id=store.id)
        return Response({'results': suggestions, 'count': len(suggestions)})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsStoreOwner])
    def add_to_cart(self, request, pk=None):
        """اضافه کردن پیشنهاد به سبد سفارش"""
        suggestion = self.get_object()
        if suggestion.is_processed:
            return Response(
                {'detail': 'این پیشنهاد قبلاً پردازش شده'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # در فاز ۶: افزودن به سبد خرید فروشگاه در store_portal
        # StorePortalService.add_to_cart(
        #     store_id=suggestion.store_id,
        #     product_id=suggestion.product_id,
        #     qty=suggestion.suggested_qty,
        # )

        suggestion.is_processed = True
        from django.utils import timezone
        suggestion.processed_at = timezone.now()
        suggestion.save(update_fields=['is_processed', 'processed_at'])

        return Response({'success': True, 'message': 'به سبد خرید اضافه شد'})


class LoyaltyTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet برای تراکنش‌های وفاداری"""
    from apps.partners.models import LoyaltyPoint
    queryset = LoyaltyPoint.objects.all()
    serializer_class = LoyaltyTransactionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['store', 'reason']
    ordering = ['-created_at']

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.role == 'store_owner':
            qs = qs.filter(store=self.request.user.profile.store)
        return qs


from django.utils import timezone  # noqa
