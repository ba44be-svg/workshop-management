"""
Dispatch Views
"""
from decimal import Decimal
from datetime import date as date_cls, datetime
from django.db.models import Sum
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


def _parse_date(s):
    """Parse YYYY-MM-DD → date. Returns None on invalid input."""
    if not s:
        return None
    if isinstance(s, date_cls):
        return s
    try:
        return datetime.fromisoformat(str(s).strip()[:10]).date()
    except (ValueError, TypeError):
        return None


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

    # =========================================================
    # D02 — تحویل به عوامل پخش
    # =========================================================

    @action(detail=False, methods=['get'])
    def settlement_check(self, request):
        """بررسی وضعیت تسویه عامل پخش — آیا تحویل تسویه‌نشده داره؟"""
        distributor_id = request.query_params.get('distributor_id')
        if not distributor_id:
            return Response(
                {'detail': 'distributor_id لازم است.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        unsettled = DispatchHeader.objects.filter(
            distributor_id=distributor_id,
            status__in=[
                DispatchHeader.DispatchStatus.PENDING,
                DispatchHeader.DispatchStatus.IN_DELIVERY,
            ],
            deleted_at__isnull=True,
        ).count()

        has_unsettled = unsettled > 0
        return Response({
            'distributor_id': int(distributor_id),
            'has_unsettled': has_unsettled,
            'unsettled_count': unsettled,
            'warning': (
                'این عامل پخش تحویل تسویه‌نشده دارد. '
                'لطفاً ابتدا تسویه کنید.'
                if has_unsettled else None
            ),
        })

    @action(detail=False, methods=['get'])
    def distributor_summary(self, request):
        """گزارش کلی عوامل پخش — جمع تحویلی، فروش، مانده و پورسانت.

        پارامترها:
            start_date, end_date: YYYY-MM-DD (اختیاری)
            distributor_id: فیلتر روی یک عامل خاص (اختیاری)
        """
        from apps.partners.models import Distributor, Store
        from apps.partners.services import DistributorStatusService
        from apps.sales.models import SalesHeader, ReturnLine

        start_date = _parse_date(request.query_params.get('start_date'))
        end_date = _parse_date(request.query_params.get('end_date'))
        distributor_id = request.query_params.get('distributor_id')

        distributors = Distributor.objects.filter(
            deleted_at__isnull=True,
            is_active=True,
        )
        if distributor_id:
            distributors = distributors.filter(id=distributor_id)
        distributors = distributors.order_by('code')

        results = []
        for d in distributors:
            # ۱) مبلغ تحویلی (از سندهای پخش)
            dispatches = DispatchHeader.objects.filter(
                distributor=d,
                deleted_at__isnull=True,
            )
            if start_date:
                dispatches = dispatches.filter(dispatch_date__gte=start_date)
            if end_date:
                dispatches = dispatches.filter(dispatch_date__lte=end_date)
            delivered_value = dispatches.aggregate(
                t=Sum('total_amount'),
            )['t'] or Decimal('0')

            # ۲) مبلغ فروخته‌شده (از سندهای فروش که این عامل ثبت کرده)
            sales_qs = SalesHeader.objects.filter(
                distributor=d,
                deleted_at__isnull=True,
            )
            if start_date:
                sales_qs = sales_qs.filter(sale_date__gte=start_date)
            if end_date:
                sales_qs = sales_qs.filter(sale_date__lte=end_date)
            sold_value = sales_qs.aggregate(
                t=Sum('total_amount'),
            )['t'] or Decimal('0')

            # ۳) مبلغ تحویل به فروشگاه‌ها — فروش‌های ثبت‌شده در فروشگاه‌های تحت پوشش این عامل
            store_ids = list(Store.objects.filter(
                distributor=d, deleted_at__isnull=True,
            ).values_list('id', flat=True))
            to_stores_value = Decimal('0')
            if store_ids:
                store_sales = SalesHeader.objects.filter(
                    store_id__in=store_ids,
                    deleted_at__isnull=True,
                )
                if start_date:
                    store_sales = store_sales.filter(sale_date__gte=start_date)
                if end_date:
                    store_sales = store_sales.filter(sale_date__lte=end_date)
                to_stores_value = store_sales.aggregate(
                    t=Sum('total_amount'),
                )['t'] or Decimal('0')

            # ۴) مبلغ برگشتی
            returned_value = Decimal('0')
            if store_ids:
                returns_qs = ReturnLine.objects.filter(
                    return_header__store_id__in=store_ids,
                    return_header__deleted_at__isnull=True,
                )
                returned_value = returns_qs.aggregate(
                    t=Sum('qty'),
                )['t'] or Decimal('0')

            # ۵) مانده (تحویل - فروخته - برگشتی)
            balance = delivered_value - sold_value - returned_value

            # ۶) پورسانت
            rate = d.commission_rate or Decimal('0')
            commission_owed = (sold_value * rate) / Decimal('100')

            results.append({
                'distributor_id': d.id,
                'distributor_code': d.code,
                'distributor_name': d.name,
                'total_delivered_value': str(delivered_value),
                'total_sold_value': str(sold_value),
                'total_to_stores_value': str(to_stores_value),
                'total_returned_value': str(returned_value),
                'balance': str(balance),
                'commission_rate': str(rate),
                'commission_owed': str(commission_owed),
                'store_count': len(store_ids),
            })

        return Response({
            'start_date': start_date.isoformat() if start_date else None,
            'end_date': end_date.isoformat() if end_date else None,
            'results': results,
            'totals': {
                'total_delivered_value': str(sum((Decimal(r['total_delivered_value']) for r in results), Decimal('0'))),
                'total_sold_value': str(sum((Decimal(r['total_sold_value']) for r in results), Decimal('0'))),
                'total_to_stores_value': str(sum((Decimal(r['total_to_stores_value']) for r in results), Decimal('0'))),
                'total_returned_value': str(sum((Decimal(r['total_returned_value']) for r in results), Decimal('0'))),
                'balance': str(sum((Decimal(r['balance']) for r in results), Decimal('0'))),
                'commission_owed': str(sum((Decimal(r['commission_owed']) for r in results), Decimal('0'))),
            },
        })

    @action(detail=False, methods=['get'])
    def distributor_detail(self, request):
        """گزارش تفصیلی: per distributor × product.

        پارامترها:
            start_date, end_date, distributor_id (همه اختیاری)
        """
        from apps.partners.models import Distributor, Store
        from apps.sales.models import SalesLine, ReturnLine

        start_date = _parse_date(request.query_params.get('start_date'))
        end_date = _parse_date(request.query_params.get('end_date'))
        distributor_id = request.query_params.get('distributor_id')

        dispatches = DispatchHeader.objects.filter(
            deleted_at__isnull=True,
            status__in=[
                DispatchHeader.DispatchStatus.PENDING,
                DispatchHeader.DispatchStatus.IN_DELIVERY,
                DispatchHeader.DispatchStatus.ARRIVED,
            ],
        )
        if distributor_id:
            dispatches = dispatches.filter(distributor_id=distributor_id)
        if start_date:
            dispatches = dispatches.filter(dispatch_date__gte=start_date)
        if end_date:
            dispatches = dispatches.filter(dispatch_date__lte=end_date)

        # جمع‌آوری تحویل‌ها به تفکیک (distributor_id × product_id)
        agg: dict = {}
        for d in dispatches.select_related('distributor').prefetch_related('lines', 'lines__product'):
            for line in d.lines.all():
                key = (d.distributor_id, line.product_id)
                if key not in agg:
                    agg[key] = {
                        'distributor_id': d.distributor_id,
                        'distributor_name': d.distributor.name if d.distributor else f'عامل #{d.distributor_id}',
                        'product_id': line.product_id,
                        'product_name': line.product.name if line.product else '—',
                        'product_code': line.product.code if line.product else '',
                        'qty_delivered': Decimal('0'),
                        'qty_sold': Decimal('0'),
                        'qty_to_stores': Decimal('0'),
                        'qty_returned': Decimal('0'),
                    }
                agg[key]['qty_delivered'] += (line.qty or Decimal('0'))

        # جمع‌آوری فروش‌ها (sales lines) به تفکیک (distributor_id × product_id)
        # - qty_sold: فروش‌هایی که distributor این عامل ثبت کرده
        # - qty_to_stores: فروش‌هایی که در فروشگاه‌های تحت پوشش این عامل ثبت شده
        distributor_ids = {k[0] for k in agg.keys()}
        if distributor_ids:
            dists = Distributor.objects.filter(id__in=list(distributor_ids))
            for dist in dists:
                # فروش‌های خود عامل
                sales_qs = SalesLine.objects.filter(
                    sale__distributor=dist,
                    sale__deleted_at__isnull=True,
                )
                if start_date:
                    sales_qs = sales_qs.filter(sale__sale_date__gte=start_date)
                if end_date:
                    sales_qs = sales_qs.filter(sale__sale_date__lte=end_date)
                for sl in sales_qs.values('product_id').annotate(
                    t=Sum('qty'),
                ):
                    key = (dist.id, sl['product_id'])
                    if key in agg:
                        agg[key]['qty_sold'] += (sl['t'] or Decimal('0'))

                # فروش به فروشگاه‌های تحت پوشش
                store_ids = list(Store.objects.filter(
                    distributor=dist, deleted_at__isnull=True,
                ).values_list('id', flat=True))
                if store_ids:
                    store_sales_qs = SalesLine.objects.filter(
                        sale__store_id__in=store_ids,
                        sale__deleted_at__isnull=True,
                    )
                    if start_date:
                        store_sales_qs = store_sales_qs.filter(sale__sale_date__gte=start_date)
                    if end_date:
                        store_sales_qs = store_sales_qs.filter(sale__sale_date__lte=end_date)
                    for sl in store_sales_qs.values('product_id').annotate(
                        t=Sum('qty'),
                    ):
                        key = (dist.id, sl['product_id'])
                        if key in agg:
                            agg[key]['qty_to_stores'] += (sl['t'] or Decimal('0'))

                # برگشت‌ها
                if store_ids:
                    returns_qs = ReturnLine.objects.filter(
                        return_header__store_id__in=store_ids,
                        return_header__deleted_at__isnull=True,
                    )
                    for rl in returns_qs.values('product_id').annotate(
                        t=Sum('qty'),
                    ):
                        key = (dist.id, rl['product_id'])
                        if key in agg:
                            agg[key]['qty_returned'] += (rl['t'] or Decimal('0'))

        results = []
        for item in agg.values():
            qty_delivered = item['qty_delivered']
            qty_sold = item['qty_sold']
            qty_to_stores = item['qty_to_stores']
            qty_returned = item['qty_returned']
            qty_balance = qty_delivered - qty_sold - qty_returned
            results.append({
                'distributor_id': item['distributor_id'],
                'distributor_name': item['distributor_name'],
                'product_id': item['product_id'],
                'product_name': item['product_name'],
                'product_code': item['product_code'],
                'qty_delivered': str(qty_delivered),
                'qty_sold': str(qty_sold),
                'qty_to_stores': str(qty_to_stores),
                'qty_returned': str(qty_returned),
                'qty_balance': str(qty_balance),
            })

        return Response({
            'start_date': start_date.isoformat() if start_date else None,
            'end_date': end_date.isoformat() if end_date else None,
            'results': results,
        })

    @action(detail=False, methods=['get'])
    def distributor_commission(self, request):
        """گزارش جمع فروش و محاسبه پورسانت.

        پارامترها:
            start_date, end_date: YYYY-MM-DD (اختیاری)
            basis: 'total' (default) or 'settled' — مبنای محاسبه پورسانت
        """
        from apps.partners.models import Distributor
        from apps.sales.models import SalesHeader, ReturnLine

        start_date = _parse_date(request.query_params.get('start_date'))
        end_date = _parse_date(request.query_params.get('end_date'))
        basis = request.query_params.get('basis', 'total')
        distributor_id = request.query_params.get('distributor_id')

        distributors = Distributor.objects.filter(
            deleted_at__isnull=True,
            is_active=True,
        )
        if distributor_id:
            distributors = distributors.filter(id=distributor_id)
        distributors = distributors.order_by('code')

        results = []
        for d in distributors:
            sales_qs = SalesHeader.objects.filter(
                distributor=d,
                deleted_at__isnull=True,
            )
            if start_date:
                sales_qs = sales_qs.filter(sale_date__gte=start_date)
            if end_date:
                sales_qs = sales_qs.filter(sale_date__lte=end_date)

            # مبنا: کل فروش یا فروش تسویه‌شده
            if basis == 'settled':
                # فروش‌هایی که در وضعیت "post" / "settle" هستند
                sales_qs = sales_qs.filter(
                    status__in=['posted', 'settle', 'invoiced'],
                )

            total_sales = sales_qs.aggregate(
                t=Sum('total_amount'),
            )['t'] or Decimal('0')

            rate = d.commission_rate or Decimal('0')
            commission_amount = (total_sales * rate) / Decimal('100')

            # وضعیت تسویه: اگر فروش بدون برگشت داشته و همه posted بوده،
            # 'settled'، وگرنه 'unsettled'
            has_unsettled_dispatches = DispatchHeader.objects.filter(
                distributor=d,
                status__in=[
                    DispatchHeader.DispatchStatus.PENDING,
                    DispatchHeader.DispatchStatus.IN_DELIVERY,
                ],
                deleted_at__isnull=True,
            ).exists()
            settlement_status = 'unsettled' if has_unsettled_dispatches else 'settled'

            results.append({
                'distributor_id': d.id,
                'distributor_code': d.code,
                'distributor_name': d.name,
                'total_sales': str(total_sales),
                'commission_rate': str(rate),
                'commission_amount': str(commission_amount),
                'settlement_status': settlement_status,
                'basis': basis,
            })

        return Response({
            'start_date': start_date.isoformat() if start_date else None,
            'end_date': end_date.isoformat() if end_date else None,
            'basis': basis,
            'results': results,
            'totals': {
                'total_sales': str(sum((Decimal(r['total_sales']) for r in results), Decimal('0'))),
                'commission_amount': str(sum((Decimal(r['commission_amount']) for r in results), Decimal('0'))),
            },
        })

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_dispatches(self, request):
        """تحویل‌های من (عامل پخش) — فقط سندهای پخش مرتبط با عامل پخشِ کاربر فعلی.

        اولویت یافتن عامل پخش:
            1) UserProfile.distributor
            2) تطبیق Distributor.mobile با username کاربر
            3) تطبیق Distributor.mobile با phone کاربر
        """
        if request.user.role != 'distributor':
            return Response(
                {'detail': 'دسترسی فقط برای عامل پخش'},
                status=status.HTTP_403_FORBIDDEN,
            )

        from apps.partners.models import Distributor
        from apps.accounts.models import UserProfile

        distributor = None
        profile = getattr(request.user, 'profile', None)
        if profile is not None and profile.distributor_id:
            distributor = profile.distributor
        if distributor is None:
            distributor = Distributor.objects.filter(
                mobile=request.user.username,
                deleted_at__isnull=True,
                is_active=True,
            ).first()
        if distributor is None and request.user.phone:
            distributor = Distributor.objects.filter(
                mobile=request.user.phone,
                deleted_at__isnull=True,
                is_active=True,
            ).first()

        if distributor is None:
            return Response(
                {'detail': 'پروفایل عامل پخش برای این کاربر یافت نشد.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        qs = DispatchHeader.objects.filter(
            distributor=distributor,
            deleted_at__isnull=True,
        ).order_by('-dispatch_date', '-id')

        # فیلتر بر اساس وضعیت (به‌طور پیش‌فرض فقط سدهای «در دسترس»)
        status_param = request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param)

        serializer = DispatchDetailSerializer(
            qs.select_related('distributor', 'vehicle').prefetch_related('lines'),
            many=True,
            context={'request': request},
        )
        return Response({
            'count': len(serializer.data),
            'results': serializer.data,
            'distributor_id': distributor.id,
            'distributor_name': distributor.name,
        })


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
