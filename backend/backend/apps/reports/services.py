"""
Reports Service — داشبورد بلادرنگ + گزارش‌های تحلیلی
"""
from decimal import Decimal
from datetime import timedelta, date, datetime
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q, F
from typing import List, Dict, Optional, Tuple


def _parse_date(s: Optional[str]) -> Optional[date]:
    """Parse YYYY-MM-DD → date. Returns None on invalid input."""
    if not s:
        return None
    if isinstance(s, date):
        return s
    try:
        return datetime.fromisoformat(str(s).strip()[:10]).date()
    except (ValueError, TypeError):
        return None


class ReportsService:
    """سرویس گزارش‌های تحلیلی"""

    @staticmethod
    def resolve_range(
        *,
        days: int = 30,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Tuple[date, date]:
        """Resolve a date range from either (start_date, end_date) or days-back.

        Returns (from_date, to_date). If start_date/end_date are provided they take
        precedence over `days`. `end_date` defaults to today.
        """
        today = timezone.now().date()
        sd = _parse_date(start_date)
        ed = _parse_date(end_date)
        if sd is not None and ed is not None:
            # Ensure from <= to
            if sd > ed:
                sd, ed = ed, sd
            return sd, ed
        if sd is not None:
            return sd, today
        if ed is not None:
            return ed - timedelta(days=max(days, 1)), ed
        return today - timedelta(days=max(days, 1)), today

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

    # =========================================================
    # Week-5 Reports — 7 new methods
    # =========================================================

    @staticmethod
    def store_receivables(*, days: int = 90,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> Dict:
        """طلبکار از فروشگاه‌ها — فروش امانی ثبت‌شده but-settled.

        نکته: در مدل SalesHeader فیلد «تسویه‌شده» وجود ندارد؛ بنابراین تمام
        فروش‌های امانیِ ثبت‌شده به‌عنوان «تسویه‌نشده» فرض می‌شوند.
        """
        try:
            from apps.sales.models import SalesHeader
            from_date, today = ReportsService.resolve_range(
                days=days, start_date=start_date, end_date=end_date,
            )

            sales_qs = (
                SalesHeader.objects
                .filter(
                    sales_type=SalesHeader.SalesType.CONSIGNMENT,
                    status=SalesHeader.SalesStatus.POSTED,
                    sale_date__gte=from_date,
                    sale_date__lte=today,
                    deleted_at__isnull=True,
                )
                .select_related('store')
                .order_by('store_id', 'sale_date')
            )

            store_map = {}
            for s in sales_qs:
                sid = s.store_id
                if sid is None:
                    continue
                if sid not in store_map:
                    store = s.store
                    store_map[sid] = {
                        'store_id': sid,
                        'store_name': store.name if store else f'فروشگاه #{sid}',
                        'store_code': store.code if store else '',
                        'total_receivable': Decimal('0'),
                        'unsettled_count': 0,
                        'sales': [],
                    }
                amount = s.total_amount or Decimal('0')
                store_map[sid]['total_receivable'] += amount
                store_map[sid]['unsettled_count'] += 1
                store_map[sid]['sales'].append({
                    'sale_id': s.id,
                    'sale_no': s.sale_no,
                    'sale_date': s.sale_date.isoformat() if s.sale_date else None,
                    'amount': str(amount),
                })

            results = []
            for item in store_map.values():
                item['total_receivable'] = str(item['total_receivable'])
                results.append(item)

            return {
                'period_days': days,
                'start_date': from_date.isoformat(),
                'end_date': today.isoformat(),
                'results': results,
            }
        except Exception as e:
            return {'error': str(e), 'results': []}

    @staticmethod
    def store_stock(*, days: int = 30,
                    start_date: Optional[str] = None,
                    end_date: Optional[str] = None) -> Dict:
        """موجودی کالا در انبارهای فروشگاه‌ها (warehouse.store_id is not null)."""
        try:
            from apps.inventory.models import StockBalance, Warehouse
            _, today = ReportsService.resolve_range(
                days=days, start_date=start_date, end_date=end_date,
            )

            store_wh_ids = list(
                Warehouse.objects
                .filter(store__isnull=False, deleted_at__isnull=True)
                .values_list('id', flat=True)
            )

            if not store_wh_ids:
                return {
                    'period_days': days,
                    'today': today.isoformat(),
                    'results': [],
                    'totals': {
                        'total_qty': '0',
                        'total_value': '0',
                        'records_count': 0,
                        'store_count': 0,
                    },
                }

            balances = (
                StockBalance.objects
                .filter(warehouse_id__in=store_wh_ids)
                .select_related('product', 'warehouse', 'warehouse__store')
            )

            results = []
            grand_qty = Decimal('0')
            grand_value = Decimal('0')
            store_ids_seen = set()

            for b in balances:
                store = b.warehouse.store
                if store is None:
                    continue
                qty = b.total_qty or Decimal('0')
                value = b.total_value or Decimal('0')
                grand_qty += qty
                grand_value += value
                store_ids_seen.add(store.id)
                results.append({
                    'store_id': store.id,
                    'store_name': store.name,
                    'product_id': b.product.id if b.product_id else None,
                    'product_name': b.product.name if b.product else '—',
                    'qty_on_hand': str(qty),
                    'value': str(value),
                })

            return {
                'period_days': days,
                'today': today.isoformat(),
                'results': results,
                'totals': {
                    'total_qty': str(grand_qty),
                    'total_value': str(grand_value),
                    'records_count': len(results),
                    'store_count': len(store_ids_seen),
                },
            }
        except Exception as e:
            return {'error': str(e), 'results': []}

    @staticmethod
    def distributor_stock(*, days: int = 30,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> Dict:
        """موجودی نزد عوامل پخش — مبتنی بر سندهای پخش فعال + برگشت‌ها."""
        try:
            from apps.dispatch.models import DispatchHeader, DispatchLine
            from apps.sales.models import ReturnLine
            from apps.partners.models import Distributor

            from_date, today = ReportsService.resolve_range(
                days=days, start_date=start_date, end_date=end_date,
            )

            dispatches = (
                DispatchHeader.objects
                .filter(
                    dispatch_date__gte=from_date,
                    dispatch_date__lte=today,
                    status__in=[
                        DispatchHeader.DispatchStatus.IN_DELIVERY,
                        DispatchHeader.DispatchStatus.ARRIVED,
                    ],
                    deleted_at__isnull=True,
                )
                .select_related('distributor')
                .prefetch_related('lines', 'lines__product')
            )

            agg: Dict = {}
            dist_ids_seen = set()
            for d in dispatches:
                dist_id = d.distributor_id
                if dist_id is None:
                    continue
                dist_ids_seen.add(dist_id)
                for line in d.lines.all():
                    key = (dist_id, line.product_id)
                    if key not in agg:
                        agg[key] = {
                            'distributor_id': dist_id,
                            'distributor_name': d.distributor.name if d.distributor else f'عامل #{dist_id}',
                            'product_id': line.product_id,
                            'product_name': line.product.name if line.product else '—',
                            'qty_delivered': Decimal('0'),
                            'qty_returned': Decimal('0'),
                            'value': Decimal('0'),
                        }
                    qty = line.qty or Decimal('0')
                    agg[key]['qty_delivered'] += qty
                    agg[key]['value'] += (line.line_total or Decimal('0'))

            # Returns grouped by distributor×product
            if dist_ids_seen:
                dists = Distributor.objects.filter(id__in=list(dist_ids_seen))
                for dist in dists:
                    store_ids = list(
                        dist.stores.filter(deleted_at__isnull=True).values_list('id', flat=True)
                    )
                    if not store_ids:
                        continue
                    ret_groups = (
                        ReturnLine.objects
                        .filter(
                            return_header__store_id__in=store_ids,
                            return_header__deleted_at__isnull=True,
                        )
                        .values('product_id')
                        .annotate(total=Sum('qty'))
                    )
                    for rg in ret_groups:
                        key = (dist.id, rg['product_id'])
                        if key in agg:
                            agg[key]['qty_returned'] += (rg['total'] or Decimal('0'))

            results = []
            for item in agg.values():
                delivered = item['qty_delivered']
                returned = item['qty_returned']
                on_hand = delivered - returned
                results.append({
                    'distributor_id': item['distributor_id'],
                    'distributor_name': item['distributor_name'],
                    'product_id': item['product_id'],
                    'product_name': item['product_name'],
                    'qty_delivered': str(delivered),
                    'qty_returned': str(returned),
                    'qty_on_hand': str(on_hand),
                    'value': str(item['value']),
                })

            return {
                'period_days': days,
                'start_date': from_date.isoformat(),
                'end_date': today.isoformat(),
                'results': results,
            }
        except Exception as e:
            return {'error': str(e), 'results': []}

    @staticmethod
    def distributor_commission(*, days: int = 30,
                               start_date: Optional[str] = None,
                               end_date: Optional[str] = None) -> Dict:
        """گزارش پورسانت عوامل پخش — مبتنی بر DistributorStatusService."""
        try:
            from apps.partners.services import DistributorStatusService
            from_date, today = ReportsService.resolve_range(
                days=days, start_date=start_date, end_date=end_date,
            )

            statuses = DistributorStatusService.get_all_distributors_status()
            results = []
            for s in statuses:
                try:
                    sold_value = Decimal(s.get('total_sold_value') or '0')
                except Exception:
                    sold_value = Decimal('0')
                try:
                    rate = Decimal(s.get('commission_rate') or '0')
                except Exception:
                    rate = Decimal('0')
                commission_owed = (sold_value * rate) / Decimal('100')

                results.append({
                    'distributor_id': s.get('distributor_id'),
                    'distributor_name': s.get('distributor_name', '—'),
                    'commission_rate': str(rate),
                    'total_delivered_value': str(s.get('total_delivered_value') or '0'),
                    'total_sold_value': str(sold_value),
                    'total_returned_value': str(s.get('total_returned_value') or '0'),
                    'commission_owed': str(commission_owed),
                })

            return {
                'period_days': days,
                'start_date': from_date.isoformat(),
                'end_date': today.isoformat(),
                'results': results,
            }
        except Exception as e:
            return {'error': str(e), 'results': []}

    @staticmethod
    def waste_report_detailed(*, days: int = 30,
                              start_date: Optional[str] = None,
                              end_date: Optional[str] = None) -> Dict:
        """گزارش تفصیلی ضایعات مبتنی بر WasteDocument + WasteLine."""
        try:
            from apps.inventory.models import WasteDocument
            from_date, today = ReportsService.resolve_range(
                days=days, start_date=start_date, end_date=end_date,
            )

            docs = (
                WasteDocument.objects
                .filter(
                    waste_date__gte=from_date,
                    waste_date__lte=today,
                    deleted_at__isnull=True,
                )
                .select_related('warehouse', 'store', 'distributor')
                .prefetch_related('lines', 'lines__product')
            )

            by_type_map: Dict = {}
            by_product_map: Dict = {}
            total_value = Decimal('0')
            details = []

            for doc in docs:
                doc_total = Decimal('0')
                lines_count = 0
                for line in doc.lines.all():
                    line_total = line.line_total or Decimal('0')
                    line_qty = line.qty or Decimal('0')
                    doc_total += line_total
                    lines_count += 1

                    pid = line.product_id
                    if pid is not None and pid not in by_product_map:
                        by_product_map[pid] = {
                            'product_id': pid,
                            'product_name': line.product.name if line.product else f'محصول #{pid}',
                            'total_qty': Decimal('0'),
                            'total_value': Decimal('0'),
                        }
                    if pid is not None:
                        by_product_map[pid]['total_qty'] += line_qty
                        by_product_map[pid]['total_value'] += line_total

                total_value += doc_total

                wt = doc.waste_type
                if wt not in by_type_map:
                    by_type_map[wt] = {
                        'waste_type': wt,
                        'waste_type_display': doc.get_waste_type_display(),
                        'total_value': Decimal('0'),
                        'count': 0,
                    }
                by_type_map[wt]['total_value'] += doc_total
                by_type_map[wt]['count'] += 1

                if doc.warehouse_id and doc.warehouse:
                    location_name = doc.warehouse.name
                elif doc.store_id and doc.store:
                    location_name = doc.store.name
                elif doc.distributor_id and doc.distributor:
                    location_name = doc.distributor.name
                else:
                    location_name = '—'

                details.append({
                    'waste_no': doc.waste_no,
                    'waste_type': wt,
                    'waste_type_display': doc.get_waste_type_display(),
                    'location_name': location_name,
                    'waste_date': doc.waste_date.isoformat() if doc.waste_date else None,
                    'total_value': str(doc_total),
                    'lines_count': lines_count,
                })

            by_type = []
            for item in by_type_map.values():
                item['total_value'] = str(item['total_value'])
                by_type.append(item)

            by_product = []
            for item in by_product_map.values():
                item['total_qty'] = str(item['total_qty'])
                item['total_value'] = str(item['total_value'])
                by_product.append(item)

            return {
                'period_days': days,
                'start_date': from_date.isoformat(),
                'end_date': today.isoformat(),
                'total_value': str(total_value),
                'by_type': by_type,
                'by_product': by_product,
                'details': details,
            }
        except Exception as e:
            return {'error': str(e), 'results': []}

    @staticmethod
    def near_expiry(*, days_threshold: int = 7) -> Dict:
        """لات‌های نزدیک به انقضا."""
        try:
            from apps.inventory.models import InventoryLot
            today = timezone.now().date()
            max_date = today + timedelta(days=days_threshold)

            lots = (
                InventoryLot.objects
                .filter(
                    expiry_date__gte=today,
                    expiry_date__lte=max_date,
                    current_qty__gt=0,
                    status=InventoryLot.LotStatus.ACTIVE,
                    deleted_at__isnull=True,
                )
                .select_related('product', 'warehouse')
                .order_by('expiry_date')
            )

            results = []
            for lot in lots:
                days_remaining = (lot.expiry_date - today).days
                results.append({
                    'lot_id': lot.id,
                    'lot_no': lot.batch_no,
                    'product_id': lot.product_id,
                    'product_name': lot.product.name if lot.product else '—',
                    'expiry_date': lot.expiry_date.isoformat(),
                    'days_remaining': int(days_remaining),
                    'qty_on_hand': str(lot.current_qty or Decimal('0')),
                    'warehouse_name': lot.warehouse.name if lot.warehouse else '—',
                })

            # مرتب‌سازی نهایی بر اساس days_remaining صعودی
            results.sort(key=lambda x: x['days_remaining'])

            return {
                'days_threshold': days_threshold,
                'today': today.isoformat(),
                'count': len(results),
                'results': results,
            }
        except Exception as e:
            return {'error': str(e), 'results': []}

    @staticmethod
    def profit_report(*, days: int = 30, group_by: str = 'product',
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None) -> Dict:
        """گزارش سود — گروه‌بندی بر اساس product / store / distributor."""
        try:
            from apps.sales.models import SalesHeader, SalesLine

            if group_by not in ('product', 'store', 'distributor'):
                return {
                    'error': f'invalid group_by: {group_by!r}; '
                             f'must be one of: product, store, distributor',
                    'results': [],
                }

            from_date, today = ReportsService.resolve_range(
                days=days, start_date=start_date, end_date=end_date,
            )

            sales_qs = (
                SalesHeader.objects
                .filter(
                    sale_date__gte=from_date,
                    sale_date__lte=today,
                    status=SalesHeader.SalesStatus.POSTED,
                    deleted_at__isnull=True,
                )
            )

            results = []
            totals = {
                'total_amount': Decimal('0'),
                'total_cost': Decimal('0'),
                'total_profit': Decimal('0'),
                'sale_count': 0,
            }

            if group_by == 'product':
                lines = (
                    SalesLine.objects
                    .filter(sale__in=sales_qs)
                    .select_related('product')
                )
                agg: Dict = {}
                for ln in lines:
                    pid = ln.product_id
                    if pid is None:
                        continue
                    if pid not in agg:
                        agg[pid] = {
                            'key_id': pid,
                            'key_name': ln.product.name if ln.product else f'محصول #{pid}',
                            'total_amount': Decimal('0'),
                            'total_cost': Decimal('0'),
                            'sale_count': 0,
                        }
                    qty = ln.qty or Decimal('0')
                    amount = qty * (ln.unit_price or Decimal('0'))
                    cost = qty * (ln.unit_cost or Decimal('0'))
                    agg[pid]['total_amount'] += amount
                    agg[pid]['total_cost'] += cost
                    agg[pid]['sale_count'] += 1

                for item in agg.values():
                    profit = item['total_amount'] - item['total_cost']
                    try:
                        margin_pct = (
                            float(profit) / float(item['total_amount']) * 100
                            if item['total_amount'] > 0 else 0.0
                        )
                    except (ZeroDivisionError, TypeError):
                        margin_pct = 0.0
                    results.append({
                        'key_id': item['key_id'],
                        'key_name': item['key_name'],
                        'total_amount': str(item['total_amount']),
                        'total_cost': str(item['total_cost']),
                        'total_profit': str(profit),
                        'margin_pct': round(margin_pct, 2),
                        'sale_count': item['sale_count'],
                    })
                    totals['total_amount'] += item['total_amount']
                    totals['total_cost'] += item['total_cost']
                    totals['total_profit'] += profit
                    totals['sale_count'] += item['sale_count']

            else:
                # store or distributor
                agg = {}
                if group_by == 'store':
                    qs = sales_qs.select_related('store')
                else:
                    qs = sales_qs.select_related('distributor')

                for sale in qs:
                    if group_by == 'store':
                        key_id = sale.store_id
                        key_name = sale.store.name if sale.store else 'فروشگاه بدون نام'
                    else:  # distributor
                        key_id = sale.distributor_id
                        if sale.distributor_id is None:
                            key_id = 0
                            key_name = 'بدون عامل پخش'
                        else:
                            key_name = sale.distributor.name if sale.distributor else f'عامل #{sale.distributor_id}'
                    if key_id not in agg:
                        agg[key_id] = {
                            'key_id': key_id,
                            'key_name': key_name,
                            'total_amount': Decimal('0'),
                            'total_cost': Decimal('0'),
                            'sale_count': 0,
                        }
                    amount = sale.total_amount or Decimal('0')
                    cost = sale.total_cost or Decimal('0')
                    agg[key_id]['total_amount'] += amount
                    agg[key_id]['total_cost'] += cost
                    agg[key_id]['sale_count'] += 1

                for item in agg.values():
                    profit = item['total_amount'] - item['total_cost']
                    try:
                        margin_pct = (
                            float(profit) / float(item['total_amount']) * 100
                            if item['total_amount'] > 0 else 0.0
                        )
                    except (ZeroDivisionError, TypeError):
                        margin_pct = 0.0
                    results.append({
                        'key_id': item['key_id'],
                        'key_name': item['key_name'],
                        'total_amount': str(item['total_amount']),
                        'total_cost': str(item['total_cost']),
                        'total_profit': str(profit),
                        'margin_pct': round(margin_pct, 2),
                        'sale_count': item['sale_count'],
                    })
                    totals['total_amount'] += item['total_amount']
                    totals['total_cost'] += item['total_cost']
                    totals['total_profit'] += profit
                    totals['sale_count'] += item['sale_count']

            totals['total_amount'] = str(totals['total_amount'])
            totals['total_cost'] = str(totals['total_cost'])
            totals['total_profit'] = str(totals['total_profit'])

            return {
                'period_days': days,
                'group_by': group_by,
                'results': results,
                'totals': totals,
            }
        except Exception as e:
            return {'error': str(e), 'results': []}
