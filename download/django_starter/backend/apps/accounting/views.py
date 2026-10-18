"""
Accounting Views
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core.permissions import IsManagerOrAccountant
from .models import (
    Account, CostCenter, FiscalPeriod, JournalTemplate,
    JournalHeader, JournalLine, ExchangeRate,
)
from .serializers import (
    AccountSerializer, CostCenterSerializer, FiscalPeriodSerializer,
    JournalTemplateSerializer, JournalHeaderSerializer, JournalDetailSerializer,
    JournalLineSerializer, ExchangeRateSerializer, CreateJournalInputSerializer,
)
from .services import JournalService
from django.utils import timezone


class AccountViewSet(viewsets.ModelViewSet):
    """ViewSet برای کدینگ حساب‌ها"""
    queryset = Account.objects.filter(deleted_at__isnull=True)
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['type', 'parent', 'is_active', 'is_postable']
    search_fields = ['code', 'name', 'description']
    ordering = ['code']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'balance']:
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsManagerOrAccountant()]

    @action(detail=False, methods=['get'])
    def tree(self, request):
        """درخت کامل کدینگ"""
        roots = self.queryset.filter(parent__isnull=True)
        serializer = AccountSerializer(roots, many=True, context={'request': request})
        return Response(serializer.data)


class CostCenterViewSet(viewsets.ModelViewSet):
    queryset = CostCenter.objects.filter(deleted_at__isnull=True)
    serializer_class = CostCenterSerializer
    permission_classes = [IsAuthenticated, IsManagerOrAccountant]
    filterset_fields = ['type', 'parent', 'is_active']
    search_fields = ['code', 'name']
    ordering = ['code']


class FiscalPeriodViewSet(viewsets.ModelViewSet):
    queryset = FiscalPeriod.objects.filter(deleted_at__isnull=True)
    serializer_class = FiscalPeriodSerializer
    permission_classes = [IsAuthenticated, IsManagerOrAccountant]
    filterset_fields = ['type', 'is_closed']
    ordering = ['-start_date']

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """بستن دوره مالی"""
        period = self.get_object()
        if period.is_closed:
            return Response(
                {'detail': 'دوره قبلاً بسته شده'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        period.is_closed = True
        period.closed_at = timezone.now()
        period.closed_by = request.user
        period.save()
        return Response(FiscalPeriodSerializer(
            period, context={'request': request}
        ).data)


class JournalTemplateViewSet(viewsets.ModelViewSet):
    queryset = JournalTemplate.objects.all()
    serializer_class = JournalTemplateSerializer
    permission_classes = [IsAuthenticated, IsManagerOrAccountant]
    filterset_fields = ['source_type', 'is_active']
    ordering = ['source_type', 'name']


class JournalHeaderViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet برای مشاهده اسناد حسابداری"""
    queryset = JournalHeader.objects.filter(deleted_at__isnull=True)
    serializer_class = JournalHeaderSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['date', 'source_type', 'status', 'period']
    search_fields = ['journal_no', 'description']
    ordering_fields = ['date', 'total_debit', 'created_at']
    ordering = ['-date', '-id']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return JournalDetailSerializer
        return JournalHeaderSerializer

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsManagerOrAccountant])
    def create_manual(self, request):
        """ساخت سند دستی حسابداری"""
        serializer = CreateJournalInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            journal = JournalService.create_manual_journal(
                date=serializer.validated_data['date'],
                description=serializer.validated_data['description'],
                lines=serializer.validated_data['lines'],
                created_by=request.user,
            )
            return Response(
                JournalDetailSerializer(journal, context={'request': request}).data,
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsManagerOrAccountant])
    def reverse(self, request, pk=None):
        """معکوس کردن سند"""
        reason = request.data.get('reason', '')
        try:
            reversal = JournalService.reverse_journal(
                journal_id=int(pk), reason=reason, reversed_by=request.user,
            )
            return Response(
                JournalDetailSerializer(reversal, context={'request': request}).data,
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=['get'])
    def trial_balance(self, request):
        """تراز آزمایشی"""
        as_of_str = request.query_params.get('as_of_date')
        as_of_date = None
        if as_of_str:
            from datetime import datetime
            as_of_date = datetime.fromisoformat(as_of_str).date()
        result = JournalService.get_trial_balance(as_of_date)
        return Response({'as_of_date': (as_of_date or timezone.now().date()).isoformat(),
                        'accounts': result})

    @action(detail=False, methods=['get'])
    def profit_loss(self, request):
        """گزارش سود و زیان"""
        from datetime import datetime
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        cost_center_id = request.query_params.get('cost_center_id')

        if date_from:
            date_from = datetime.fromisoformat(date_from).date()
        if date_to:
            date_to = datetime.fromisoformat(date_to).date()
        if cost_center_id:
            cost_center_id = int(cost_center_id)

        report = JournalService.get_profit_loss(date_from, date_to, cost_center_id)
        return Response(report)


class JournalLineViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet برای خطوط سند"""
    queryset = JournalLine.objects.all()
    serializer_class = JournalLineSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['journal', 'account', 'cost_center']
    ordering = ['journal', 'id']


class ExchangeRateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ExchangeRate.objects.all()
    serializer_class = ExchangeRateSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['currency']
    ordering = ['-effective_date']
