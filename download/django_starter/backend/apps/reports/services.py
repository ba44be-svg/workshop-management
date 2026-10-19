"""
Reports Service — داشبورد بلادرنگ + گزارش‌های تحلیلی
"""
from decimal import Decimal
from datetime import timedelta, date
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q, F
from typing import List, Dict


class ReportsService:
    """سرویس گزارش‌های تحلیلی"""

    @staticmethod
    def get_dashboard_summary(*, days: int = 30) -> Dict:
        """خلاصه داشبورد مدیر"""
        today = timezone.now().date()
        from_date = today - timedelta(days=days)

        # ----- فروش -----
        from apps.sales.models import SalesHeader
        sales = SalesHeader.objects.filter(
            sale_date__gte=from_date, sale_date__lte=today,
            status=SalesHeader.SalesStatus.POSTED,
            deleted_at__isnull=True,
        )
        total_sales_amount = sales.aggregate(t=Sum('total_amount'))['t'] or Decimal('0')
        total_sales_cost = sales.aggregate(t=Sum('total_cost'))['t'] or Decimal('0')
        total_profit = total_sales_amount - total_sales_cost

        # ----- پخش -----
        from apps.dispatch.models import DispatchHeader
        active_dispatches = DispatchHeader.objects.filter(
            dispatch_date=today,
            status__in=[
                DispatchHeader.DispatchStatus.PENDING,
                DispatchHeader.DispatchStatus.IN_DELIVERY,
            ],
        ).count()

        # ----- تأیید -----
        from apps.approval_workflow.models import ApprovalQueue, ApprovalStatus
        pending_approvals = ApprovalQueue.objects.filter(
            status=ApprovalStatus.PENDING,
        ).count()

        # ----- لات‌های نزدیک به انقضا -----
        from apps.inventory.models import InventoryLot
        near_expiry = InventoryLot.objects.filter(
            expiry_date__lte=today + timedelta(days=5),
            expiry_date__gt=today,
            current_qty__gt=0,
            status=InventoryLot.LotStatus.ACTIVE,
            deleted_at__isnull=True,
        ).count()

        # ----- محصولات کم‌موجودی -----
        from apps.inventory.models import StockBalance
        low_stock = StockBalance.objects.filter(total_qty__lt=10).count()

        # ----- فروشگاه‌های فعال -----
        from apps.partners.models import Store
        active_stores = Store.objects.filter(
            is_active=True, deleted_at__isnull=True,
        ).count()

        # ----- عوامل فعال -----
        from apps.partners.models import Distributor
        active_distributors = Distributor.objects.filter(
            is_active=True, deleted_at__isnull=True,
        ).count()

        return {
            'today': today.isoformat(),
            'period_days': days,
            'sales': {
                'total_amount': str(total_sales_amount),
                'total_cost': str(total_sales_cost),
                'total_profit': str(total_profit),
                'count': sales.count(),
                'consignment_count': sales.filter(
                    sales_type=SalesHeader.SalesType.CONSIGNMENT,
                ).count(),
                'firm_count': sales.filter(
                    sales_type=SalesHeader.SalesType.FIRM,
                ).count(),
            },
            'dispatches': {
                'active_count': active_dispatches,
            },
            'approvals': {
                'pending_count': pending_approvals,
            },
            'inventory': {
                'near_expiry_lots': near_expiry,
                'low_stock_products': low_stock,
            },
            'partners': {
                'active_stores': active_stores,
                'active_distributors': active_distributors,
            },
        }

    @staticmethod
    def get_geo_heatmap(*, days: int = 30) -> List[Dict]:
        """گزارش جغرافیایی Heatmap فروش"""
        from apps.partners.models import Store
        from apps.sales.models import SalesHeader
        from django.db.models import Sum

        today = timezone.now().date()
        from_date = today - timedelta(days=days)

        stores = Store.objects.filter(
            deleted_at__isnull=True,
            is_active=True,
            geo_lat__isnull=False,
        )

        results = []
        for store in stores:
            total_sales = SalesHeader.objects.filter(
                store=store,
                sale_date__gte=from_date,
                sale_date__lte=today,
                status=SalesHeader.SalesStatus.POSTED,
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')

            # شدت رنگ بر اساس میزان فروش
            total_amount = float(total_sales)
            if total_amount > 100000000:
                intensity = 'very_high'
            elif total_amount > 50000000:
                intensity = 'high'
            elif total_amount > 10000000:
                intensity = 'medium'
            elif total_amount > 1000000:
                intensity = 'low'
            else:
                intensity = 'very_low'

            results.append({
                'store_id': store.id,
                'name': store.name,
                'lat': float(store.geo_lat),
                'lng': float(store.geo_lng),
                'total_sales': str(total_sales),
                'intensity': intensity,
                'tier': store.tier,
                'sales_count': SalesHeader.objects.filter(
                    store=store,
                    sale_date__gte=from_date,
                    status=SalesHeader.SalesStatus.POSTED,
                ).count(),
            })

        return results

    @staticmethod
    def get_waste_report(*, days: int = 30) -> Dict:
        """گزارش ضایعات تولید"""
        from apps.production.models import ProductionBatch
        today = timezone.now().date()
        from_date = today - timedelta(days=days)

        batches = ProductionBatch.objects.filter(
            end_at__date__gte=from_date,
            end_at__date__lte=today,
            status=ProductionBatch.BatchStatus.COMPLETED,
        )

        summary = batches.aggregate(
            total_batches=Count('id'),
            total_produced=Sum('actual_qty'),
            total_waste=Sum('waste_qty'),
            avg_cost=Avg('weighted_avg_cost'),
        )

        # محاسبه درصد ضایعات
        total_produced = summary['total_produced'] or Decimal('0')
        total_waste = summary['total_waste'] or Decimal('0')
        waste_percentage = (
            float(total_waste) / float(total_produced + total_waste) * 100
            if (total_produced + total_waste) > 0 else 0
        )

        # ----- رتبه‌بندی محصولات بر اساس ضایعات -----
        from apps.products.models import Product
        products_waste = []
        for product in Product.objects.filter(is_active=True):
            product_batches = batches.filter(product=product)
            p_produced = product_batches.aggregate(t=Sum('actual_qty'))['t'] or Decimal('0')
            p_waste = product_batches.aggregate(t=Sum('waste_qty'))['t'] or Decimal('0')
            if p_produced + p_waste > 0:
                p_waste_pct = float(p_waste) / float(p_produced + p_waste) * 100
                products_waste.append({
                    'product_id': product.id,
                    'product_code': product.code,
                    'product_name': product.name,
                    'produced': str(p_produced),
                    'waste': str(p_waste),
                    'waste_pct': round(p_waste_pct, 2),
                })

        # مرتب‌سازی بر اساس درصد ضایعات (نزولی)
        products_waste.sort(key=lambda x: x['waste_pct'], reverse=True)

        return {
            'date_from': from_date.isoformat(),
            'date_to': today.isoformat(),
            'summary': {
                'total_batches': summary['total_batches'] or 0,
                'total_produced': str(total_produced),
                'total_waste': str(total_waste),
                'avg_cost': str(summary['avg_cost'] or 0),
                'waste_percentage': round(waste_percentage, 2),
            },
            'products_ranking': products_waste[:20],  # top 20
        }

    @staticmethod
    def get_top_products(*, days: int = 30, limit: int = 20) -> List[Dict]:
        """محصولات پرفروش"""
        from apps.sales.models import SalesLine, SalesHeader
        from apps.products.models import Product
        from django.db.models import Sum

        today = timezone.now().date()
        from_date = today - timedelta(days=days)

        top = (
            SalesLine.objects
            .filter(
                sale__sale_date__gte=from_date,
                sale__sale_date__lte=today,
                sale__status=SalesHeader.SalesStatus.POSTED,
            )
            .values('product_id')
            .annotate(
                total_qty=Sum('qty'),
                total_amount=Sum('qty') * F('unit_price'),
            )
            .order_by('-total_qty')[:limit]
        )

        results = []
        for item in top:
            product = Product.objects.get(id=item['product_id'])
            results.append({
                'product_id': product.id,
                'product_code': product.code,
                'product_name': product.name,
                'total_qty': str(item['total_qty']),
                'total_amount': str(item['total_amount']),
            })
        return results

    @staticmethod
    def get_top_stores(*, days: int = 30, limit: int = 20) -> List[Dict]:
        """فروشگاه‌های پرفروش"""
        from apps.sales.models import SalesHeader
        from apps.partners.models import Store
        from django.db.models import Sum, Count

        today = timezone.now().date()
        from_date = today - timedelta(days=days)

        top = (
            SalesHeader.objects
            .filter(
                sale_date__gte=from_date,
                sale_date__lte=today,
                status=SalesHeader.SalesStatus.POSTED,
            )
            .values('store_id')
            .annotate(
                total_amount=Sum('total_amount'),
                sales_count=Count('id'),
            )
            .order_by('-total_amount')[:limit]
        )

        results = []
        for item in top:
            store = Store.objects.get(id=item['store_id'])
            results.append({
                'store_id': store.id,
                'store_name': store.name,
                'store_code': store.code,
                'total_amount': str(item['total_amount']),
                'sales_count': item['sales_count'],
                'tier': store.tier,
            })
        return results

    @staticmethod
    def get_top_distributors(*, days: int = 30, limit: int = 10) -> List[Dict]:
        """عوامل پخش برتر"""
        from apps.dispatch.models import DispatchHeader
        from apps.partners.models import Distributor
        from django.db.models import Sum, Count

        today = timezone.now().date()
        from_date = today - timedelta(days=days)

        top = (
            DispatchHeader.objects
            .filter(
                dispatch_date__gte=from_date,
                dispatch_date__lte=today,
                status=DispatchHeader.DispatchStatus.ARRIVED,
            )
            .values('distributor_id')
            .annotate(
                total_amount=Sum('total_amount'),
                dispatches_count=Count('id'),
            )
            .order_by('-total_amount')[:limit]
        )

        results = []
        for item in top:
            dist = Distributor.objects.get(id=item['distributor_id'])
            results.append({
                'distributor_id': dist.id,
                'distributor_name': dist.name,
                'total_amount': str(item['total_amount']),
                'dispatches_count': item['dispatches_count'],
                'commission_rate': str(dist.commission_rate),
            })
        return results

    @staticmethod
    def get_sales_trend(*, days: int = 30) -> List[Dict]:
        """روند فروش روزانه"""
        from apps.sales.models import SalesHeader
        from django.db.models import Sum, Count

        today = timezone.now().date()
        from_date = today - timedelta(days=days)

        daily_sales = (
            SalesHeader.objects
            .filter(
                sale_date__gte=from_date,
                sale_date__lte=today,
                status=SalesHeader.SalesStatus.POSTED,
            )
            .values('sale_date')
            .annotate(
                total_amount=Sum('total_amount'),
                sales_count=Count('id'),
            )
            .order_by('sale_date')
        )

        return [
            {
                'date': d['sale_date'].isoformat(),
                'total_amount': str(d['total_amount']),
                'sales_count': d['sales_count'],
            }
            for d in daily_sales
        ]
