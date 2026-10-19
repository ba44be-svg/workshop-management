"""
Store Portal Views — Endpointهای پورتال B2B فروشگاه‌ها
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core.permissions import IsManager, IsStoreOwner
from .models import StoreOrder, StoreOrderLine, StoreNotification, StoreDashboard
from .serializers import (
    StoreOrderSerializer, StoreOrderDetailSerializer,
    StoreOrderLineSerializer, StoreNotificationSerializer,
    StoreDashboardSerializer, CreateOrderInputSerializer,
)
from .services import StorePortalService


class StoreOrderViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet برای سفارش‌های فروشگاه"""
    queryset = StoreOrder.objects.filter(deleted_at__isnull=True)
    serializer_class = StoreOrderSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['store', 'status', 'payment_status', 'order_date']
    search_fields = ['order_no', 'notes']
    ordering = ['-order_date', '-id']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return StoreOrderDetailSerializer
        return StoreOrderSerializer

    def get_queryset(self):
        """فروشگاه‌ها فقط سفارش‌های خودشان را می‌بینند"""
        qs = super().get_queryset()
        if self.request.user.role == 'store_owner':
            qs = qs.filter(store=self.request.user.profile.store)
        return qs

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsStoreOwner])
    def create_order(self, request):
        """ساخت سفارش جدید"""
        serializer = CreateOrderInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # دریافت store_id از پروفایل کاربر
        store = request.user.profile.store
        if not store:
            return Response(
                {'detail': 'فروشگاهی برای این کاربر ثبت نشده'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            order = StorePortalService.create_order(
                store_id=store.id,
                lines=serializer.validated_data['lines'],
                notes=serializer.validated_data.get('notes', ''),
                expected_delivery=serializer.validated_data.get('expected_delivery'),
                delivery_address=serializer.validated_data.get('delivery_address', ''),
                created_by=request.user,
            )
            return Response(
                StoreOrderDetailSerializer(order, context={'request': request}).data,
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsStoreOwner])
    def cancel(self, request, pk=None):
        """لغو سفارش"""
        try:
            order = StorePortalService.cancel_order(
                order_id=int(pk), canceled_by=request.user,
            )
            return Response(StoreOrderSerializer(
                order, context={'request': request}
            ).data)
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsStoreOwner])
    def mark_received(self, request, pk=None):
        """تأیید دریافت کالا"""
        try:
            order = StorePortalService.mark_received(
                order_id=int(pk), received_by=request.user,
            )
            return Response(StoreOrderSerializer(
                order, context={'request': request}
            ).data)
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsManager])
    def approve(self, request, pk=None):
        """تأیید سفارش توسط مدیر"""
        order = self.get_object()
        if order.status != 'submitted':
            return Response(
                {'detail': f'سفارش در وضعیت {order.status} است'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from apps.approval_workflow.services import ApprovalService
        from apps.approval_workflow.models import ApprovalQueue

        approval = ApprovalQueue.objects.filter(
            ref_doc_type='store_order', ref_doc_id=order.id,
        ).first()
        if approval:
            try:
                ApprovalService.approve(
                    approval_id=approval.id,
                    approved_by_id=request.user.id,
                    reason='تأیید توسط مدیر',
                )
                order.refresh_from_db()
                return Response(StoreOrderDetailSerializer(
                    order, context={'request': request}
                ).data)
            except Exception as e:
                return Response(
                    {'detail': str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(
            {'detail': 'آیتم تأیید یافت نشد'},
            status=status.HTTP_404_NOT_FOUND,
        )


class StorePortalViewSet(viewsets.ViewSet):
    """ViewSet برای endpointهای پورتال فروشگاه (catalog, balance, etc.)"""

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsStoreOwner])
    def catalog(self, request):
        """کاتالوگ محصولات با قیمت مناسب برای فروشگاه"""
        store = request.user.profile.store
        if not store:
            return Response(
                {'detail': 'فروشگاهی برای این کاربر ثبت نشده'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        catalog = StorePortalService.get_catalog(store.id)
        return Response({'results': catalog, 'store_tier': store.tier})

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsStoreOwner])
    def balance(self, request):
        """مانده حساب فروشگاه"""
        store = request.user.profile.store
        if not store:
            return Response(
                {'detail': 'فروشگاهی برای این کاربر ثبت نشده'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(StorePortalService.get_balance(store.id))

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsStoreOwner])
    def order_history(self, request):
        """تاریخچه سفارش‌ها"""
        store = request.user.profile.store
        orders = StorePortalService.get_order_history(store.id)
        return Response({'results': orders})

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsStoreOwner])
    def notifications(self, request):
        """اعلان‌های فروشگاه"""
        store = request.user.profile.store
        unread_only = request.query_params.get('unread') == 'true'
        notifications = StorePortalService.get_notifications(
            store.id, unread_only=unread_only,
        )
        serializer = StoreNotificationSerializer(notifications, many=True)
        return Response({'results': serializer.data})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsStoreOwner])
    def mark_notification_read(self, request, pk=None):
        """علامت‌گذاری اعلان به‌عنوان خوانده‌شده"""
        StorePortalService.mark_notification_read(notification_id=int(pk))
        return Response({'success': True})

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsStoreOwner])
    def dashboard(self, request):
        """داشبورد فروشگاه"""
        store = request.user.profile.store
        dashboard = StoreDashboard.refresh_for_store(store.id)
        serializer = StoreDashboardSerializer(dashboard)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsStoreOwner])
    def smart_reorder(self, request):
        """پیشنهاد سفارش هوشمند"""
        store = request.user.profile.store
        from apps.loyalty.services import SmartReorderService
        suggestions = SmartReorderService.generate_suggestions(store_id=store.id)
        return Response({'results': suggestions})
