"""
Partners Service — منطق کسب‌وکار برای عوامل پخش
"""
from decimal import Decimal
from django.db.models import Sum, F, Q
from django.utils import timezone
from .models import Distributor, Store


class DistributorStatusService:
    """سرویس محاسبه‌ی وضعیت مالی عامل پخش"""

    @staticmethod
    def get_distributor_status(distributor: Distributor) -> dict:
        """
        محاسبه‌ی وضعیت مالی یک عامل پخش.

        برمی‌گرداند:
            - total_delivered_value: ارزش کل کالای تحویل‌شده به عامل (از سند پخش)
            - total_sold_value: ارزش کل کالای فروخته‌شده توسط عامل (از سند فروش)
            - total_returned_value: ارزش کل کالای برگشتی از عامل
            - commission_rate: درصد پورسانت
            - commission_owed: پورسانت قابل پرداخت (sold_value * rate / 100)
            - balance: بدهکار/طلبکار (commission_owed - settled_commission)
            - store_count: تعداد فروشگاه‌های تحت پوشش
        """
        from apps.dispatch.models import DispatchHeader
        from apps.sales.models import SalesHeader, ReturnHeader

        # ۱) ارزش کل کالای تحویل‌شده به عامل (از سندهای پخش)
        delivered = DispatchHeader.objects.filter(
            distributor=distributor,
            deleted_at__isnull=True,
        ).aggregate(
            total=Sum('total_amount'),
        )['total'] or Decimal('0')

        # ۲) ارزش کل کالای فروخته‌شده توسط عامل (از سندهای فروش)
        sold = SalesHeader.objects.filter(
            distributor=distributor,
            deleted_at__isnull=True,
        ).aggregate(
            total=Sum('total_amount'),
        )['total'] or Decimal('0')

        # ۳) ارزش کل کالای برگشتی (از سندهای برگشت فروش)
        # فروشگاه‌های تحت پوشش این عامل
        store_ids = list(Store.objects.filter(
            distributor=distributor,
        ).values_list('id', flat=True))

        returned = Decimal('0')
        if store_ids:
            returned = ReturnHeader.objects.filter(
                store_id__in=store_ids,
                deleted_at__isnull=True,
            ).aggregate(
                total=Sum('lines__qty') * Decimal('1'),  # تعداد برگشتی
            )['total'] or Decimal('0')

        # ۴) تعداد فروشگاه‌های تحت پوشش
        store_count = Store.objects.filter(
            distributor=distributor,
            deleted_at__isnull=True,
            is_active=True,
        ).count()

        # ۵) پورسانت قابل پرداخت
        commission_rate = distributor.commission_rate or Decimal('0')
        commission_owed = (sold * commission_rate) / Decimal('100')

        # ۶) موجودی فعلی (به‌صورت ساده — در نسخه‌ی کامل، سند پرداخت ثبت می‌شه)
        # فعلاً فرض می‌کنیم چیزی پرداخت نشده
        balance = commission_owed

        return {
            'distributor_id': distributor.id,
            'distributor_name': distributor.name,
            'distributor_code': distributor.code,
            'mobile': distributor.mobile,
            'commission_rate': str(commission_rate),
            'total_delivered_value': str(delivered),
            'total_sold_value': str(sold),
            'total_returned_value': str(returned),
            'commission_owed': str(commission_owed),
            'balance': str(balance),
            'store_count': store_count,
            'is_active': distributor.is_active,
        }

    @staticmethod
    def get_all_distributors_status():
        """محاسبه‌ی وضعیت همه‌ی عوامل پخش فعال"""
        distributors = Distributor.objects.filter(
            deleted_at__isnull=True,
        ).order_by('code')
        return [
            DistributorStatusService.get_distributor_status(d)
            for d in distributors
        ]
