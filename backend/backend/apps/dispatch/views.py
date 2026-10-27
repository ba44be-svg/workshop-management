"""
Dispatch Views
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core.permissions import IsManager, IsManagerOrDistributor
from .models import Vehicle, Route, DispatchHeader, DispatchLine, SalespersonVisit
from .serializers import (
    VehicleSerializer, RouteSerializer, DispatchHeaderSerializer,
    DispatchDetailSerializer, DispatchLineSerializer, SalespersonVisitSerializer,
    CreateDispatchInputSerializer,
)
from .services import DispatchService


class VehicleViewSet(viewsets.ModelViewSet):
    """ViewSet برای خودروها"""
    queryset = Vehicle.objects.filter(deleted_at__isnull=True)
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['plate', 'driver_name']
    ordering = ['plate']


class RouteViewSet(viewsets.ModelViewSet):
    """ViewSet برای مسیرها"""
    queryset = Route.objects.filter(deleted_at__isnull=True)
    serializer_class = RouteSerializer
    permission_classes = [IsAuthenticated, IsManager]
    filterset_fields = ['distributor', 'day_of_week', 'is_active']
    ordering = ['distributor', 'day_of_week']


class DispatchHeaderViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet برای مشاهده اسناد پخش"""
    queryset = DispatchHeader.objects.filter(deleted_at__isnull=True)
    permission_classes = [IsAuthenticated]
    filterset_fields = ['distributor', 'status', 'dispatch_date', 'vehicle']
    search_fields = ['dispatch_no', 'distributor__name', 'notes']
    ordering_fields = ['dispatch_date', 'total_amount', 'created_at']
    ordering = ['-dispatch_date']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DispatchDetailSerializer
        return DispatchHeaderSerializer

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsManagerOrDistributor])
    def create_dispatch(self, request):
        """ساخت سند پخش جدید با انتقال خودکار موجودی به انبار فروشگاه"""
        serializer = CreateDispatchInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            dispatch = DispatchService.create_dispatch(
                distributor_id=serializer.validated_data['distributor_id'],
                dispatch_date=serializer.validated_data.get('dispatch_date'),
                vehicle_id=serializer.validated_data.get('vehicle_id'),
                lines=serializer.validated_data['lines'],
                notes=serializer.validated_data.get('notes', ''),
                created_by=request.user,
            )
            return Response(
                DispatchDetailSerializer(dispatch, context={'request': request}).data,
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=['post'])
    def start_delivery(self, request, pk=None):
        """شروع تحویل"""
        try:
            dispatch = DispatchService.start_delivery(
                dispatch_id=int(pk), started_by=request.user,
            )
            return Response(DispatchHeaderSerializer(
                dispatch, context={'request': request}
            ).data)
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=['post'])
    def mark_arrived(self, request, pk=None):
        """تحویل شد"""
        try:
            dispatch = DispatchService.mark_arrived(
                dispatch_id=int(pk), arrived_by=request.user,
            )
            return Response(DispatchHeaderSerializer(
                dispatch, context={'request': request}
            ).data)
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """لغو پخش (با بازگشت موجودی به انبار اصلی)"""
        reason = request.data.get('reason', '')
        try:
            dispatch = DispatchService.cancel_dispatch(
                dispatch_id=int(pk), reason=reason, canceled_by=request.user,
            )
            return Response(DispatchHeaderSerializer(
                dispatch, context={'request': request}
            ).data)
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class DispatchLineViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet فقط خواندنی برای اقلام پخش"""
    queryset = DispatchLine.objects.all()
    serializer_class = DispatchLineSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['dispatch', 'product', 'lot', 'dest_store']
    ordering = ['dispatch']


class SalespersonVisitViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet برای سرکشی‌ها"""
    queryset = SalespersonVisit.objects.all()
    serializer_class = SalespersonVisitSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['distributor', 'store', 'visit_date']
    ordering = ['-visit_date']
