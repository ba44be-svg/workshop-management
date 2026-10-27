"""
Workshop Views
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from core.permissions import IsManager, IsManagerOrStorekeeper, IsManagerOrAccountant
from .models import (
    Contractor, Employee, PurchaseHeader, PurchaseReturn, WorkshopIssue, WorkshopReturn,
)
from .serializers import (
    ContractorSerializer,
    EmployeeSerializer,
    PurchaseHeaderSerializer, PurchaseDetailSerializer,
    CreatePurchaseInputSerializer,
    PurchaseReturnSerializer, PurchaseReturnDetailSerializer,
    CreatePurchaseReturnInputSerializer,
    WorkshopIssueSerializer, WorkshopIssueDetailSerializer,
    CreateIssueInputSerializer,
    WorkshopReturnSerializer, WorkshopReturnDetailSerializer,
    CreateReturnInputSerializer,
)
from .services import PurchaseService, PurchaseReturnService, WorkshopService


class ContractorViewSet(viewsets.ModelViewSet):
    """ViewSet برای کارپردازها"""
    queryset = Contractor.objects.filter(deleted_at__isnull=True)
    serializer_class = ContractorSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['is_active']
    search_fields = ['code', 'name', 'mobile', 'workshop_name']
    ordering = ['code']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsManagerOrStorekeeper()]


class EmployeeViewSet(viewsets.ModelViewSet):
    """ViewSet برای کارکنان (پرسنل کارگاه)."""
    queryset = Employee.objects.filter(deleted_at__isnull=True)
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['is_active', 'workshop', 'position']
    search_fields = ['code', 'first_name', 'last_name', 'national_id',
                     'mobile', 'phone', 'position']
    ordering = ['code']

    def get_permissions(self):
        # خواندن برای همه‌ی کاربران احراز هویت‌شده
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        # ساخت/ویرایش/حذف = فقط مدیر یا انباردار
        return [IsAuthenticated(), IsManagerOrStorekeeper()]


class PurchaseViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet فقط‌خواندنی برای اسناد خرید + اکشن create_purchase"""
    queryset = PurchaseHeader.objects.filter(deleted_at__isnull=True)
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['contractor', 'warehouse', 'status', 'purchase_date']
    search_fields = ['purchase_no', 'notes', 'contractor__name', 'contractor__code']
    ordering_fields = ['purchase_date', 'purchase_no', 'total_amount']
    ordering = ['-purchase_date', '-id']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PurchaseDetailSerializer
        return PurchaseHeaderSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsManagerOrAccountant()]

    @action(detail=False, methods=['post'])
    def create_purchase(self, request):
        """ساخت سند خرید مواد اولیه با auto-journal و auto-lot"""
        serializer = CreatePurchaseInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            # تولید purchase_no اگر ارسال نشده باشد
            purchase_no = data.get('purchase_no') or PurchaseService.generate_purchase_no()

            purchase = PurchaseService.create_purchase(
                purchase_no=purchase_no,
                purchase_date=data['purchase_date'],
                contractor_id=data['contractor_id'],
                warehouse_id=data['warehouse_id'],
                cash_account_id=data['cash_account_id'],
                lines=[
                    {
                        'product_id': l.get('product_id'),
                        'product_name': l.get('product_name'),
                        'product_code': l.get('product_code'),
                        'qty': l['qty'],
                        'unit_price': l['unit_price'],
                        'shelf_life_days': l.get('shelf_life_days', 15),
                        'expiry_date': l.get('expiry_date'),
                        'lot_no': l.get('lot_no'),
                        'unit_id': l.get('unit_id'),
                    }
                    for l in data['lines']
                ],
                notes=data.get('notes', ''),
                created_by=request.user,
            )
            return Response(
                PurchaseDetailSerializer(purchase, context={'request': request}).data,
                status=status.HTTP_201_CREATED,
            )
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkshopIssueViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet فقط‌خواندنی برای حواله‌های کارگاه + اکشن create_issue"""
    queryset = WorkshopIssue.objects.filter(deleted_at__isnull=True)
    permission_classes = [IsAuthenticated]
    filterset_fields = ['contractor', 'from_warehouse', 'to_warehouse',
                        'status', 'issue_date']
    search_fields = ['issue_no', 'notes', 'contractor__name', 'contractor__code']
    ordering = ['-issue_date', '-id']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return WorkshopIssueDetailSerializer
        return WorkshopIssueSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsManagerOrStorekeeper()]

    @action(detail=False, methods=['post'])
    def create_issue(self, request):
        """ساخت حواله کارگاه با FEFO + auto-journal"""
        serializer = CreateIssueInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            issue = WorkshopService.create_issue(
                issue_no=data['issue_no'],
                issue_date=data['issue_date'],
                contractor_id=data.get('contractor_id'),
                employee_id=data.get('employee_id'),
                from_warehouse_id=data['from_warehouse_id'],
                to_warehouse_id=data['to_warehouse_id'],
                production_batch_id=data.get('production_batch_id'),
                lines=[
                    {
                        'product_id': l['product_id'],
                        'qty': l['qty'],
                    }
                    for l in data['lines']
                ],
                notes=data.get('notes', ''),
                created_by=request.user,
            )
            return Response(
                WorkshopIssueDetailSerializer(issue, context={'request': request}).data,
                status=status.HTTP_201_CREATED,
            )
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkshopReturnViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet فقط‌خواندنی برای برگشت‌های کارگاه + اکشن create_return"""
    queryset = WorkshopReturn.objects.filter(deleted_at__isnull=True)
    permission_classes = [IsAuthenticated]
    filterset_fields = ['contractor', 'issue', 'status', 'return_date']
    search_fields = ['return_no', 'reason', 'contractor__name']
    ordering = ['-return_date', '-id']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return WorkshopReturnDetailSerializer
        return WorkshopReturnSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsManagerOrStorekeeper()]

    @action(detail=False, methods=['post'])
    def create_return(self, request):
        """ساخت برگشت کارگاه با auto-journal"""
        serializer = CreateReturnInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            return_doc = WorkshopService.create_return(
                return_no=data['return_no'],
                return_date=data['return_date'],
                issue_id=data['issue_id'],
                lines=[
                    {
                        'issue_line_id': l['issue_line_id'],
                        'qty': l['qty'],
                    }
                    for l in data['lines']
                ],
                reason=data.get('reason', ''),
                created_by=request.user,
            )
            return Response(
                WorkshopReturnDetailSerializer(return_doc, context={'request': request}).data,
                status=status.HTTP_201_CREATED,
            )
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# PurchaseReturn ViewSet
# ============================================================================

class PurchaseReturnViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet برای برگشت‌های خرید + اکشن create_return"""

    queryset = PurchaseReturn.objects.filter(deleted_at__isnull=True)
    serializer_class = PurchaseReturnDetailSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['purchase', 'contractor', 'warehouse', 'status', 'return_date']

    def get_serializer_class(self):
        if self.action in ['list']:
            return PurchaseReturnSerializer
        return PurchaseReturnDetailSerializer

    @action(detail=False, methods=['post'])
    def create_return(self, request):
        """ساخت سند برگشت از خرید با auto-journal و کاهش موجودی"""
        serializer = CreatePurchaseReturnInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            return_no = data.get('return_no') or PurchaseReturnService.generate_return_no()

            return_doc = PurchaseReturnService.create_return(
                return_no=return_no,
                return_date=data['return_date'],
                purchase_id=data['purchase_id'],
                lines=[
                    {
                        'purchase_line_id': l['purchase_line_id'],
                        'qty': l['qty'],
                    }
                    for l in data['lines']
                ],
                reason=data.get('reason', ''),
                created_by=request.user,
            )
            return Response(
                PurchaseReturnDetailSerializer(return_doc, context={'request': request}).data,
                status=status.HTTP_201_CREATED,
            )
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
