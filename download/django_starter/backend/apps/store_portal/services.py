"""
Store Portal Service — منطق پورتال فروشگاه (سفارش، کاتالوگ، مانده)
"""
from decimal import Decimal
from typing import List, Optional
from django.db import transaction
from django.utils import timezone
from django.db.models import Sum
from .models import StoreOrder, StoreOrderLine, StoreNotification, StoreDashboard
from apps.products.models import Product, PricingRule
from apps.partners.models import Store
from core.exceptions import CreditLimitExceededError


class StorePortalService:
    """سرویس پورتال فروشگاه"""

    @staticmethod
    @transaction.atomic
    def create_order(
        *,
        store_id: int,
        lines: List[dict],
        notes: str = '',
        expected_delivery=None,
        delivery_address: str = '',
        created_by=None,
    ) -> StoreOrder:
        """
        ساخت سفارش جدید توسط فروشگاه.

        خطوط ورودی:
            [{'product_id': 1, 'qty': 30}, {'product_id': 5, 'qty': 20}, ...]
        """

        store = Store.objects.get(id=store_id)

        # ۱. محاسبه مبلغ کل با قیمت مناسب برای لایه فروشگاه
        total_amount = Decimal('0')
        total_qty = Decimal('0')
        processed_lines = []

        for line_data in lines:
            product = Product.objects.get(id=line_data['product_id'])
            qty = Decimal(line_data['qty'])

            # دریافت قیمت مناسب بر اساس لایه فروشگاه
            unit_price = StorePortalService._get_price_for_store(
                product=product, store=store,
            )

            line_total = qty * unit_price
            total_amount += line_total
            total_qty += qty

            processed_lines.append({
                'product_id': product.id,
                'qty': qty,
                'unit_price': unit_price,
                'is_smart_suggestion': line_data.get('is_smart_suggestion', False),
                'notes': line_data.get('notes', ''),
            })

        # ۲. کنترل سقف اعتبار فروشگاه
        if store.current_credit + total_amount > store.credit_limit:
            available = store.credit_limit - store.current_credit
            raise CreditLimitExceededError(
                f'سقف اعتبار کافی نیست. درخواست: {total_amount} ریال، '
                f'موجود: {available} ریال'
            )

        # ۳. ساخت سفارش
        order = StoreOrder.objects.create(
            order_no=StorePortalService._generate_order_number(),
            store_id=store_id,
            order_date=timezone.now().date(),
            status=StoreOrder.OrderStatus.SUBMITTED,
            total_amount=total_amount,
            total_qty=total_qty,
            expected_delivery=expected_delivery,
            delivery_address=delivery_address,
            notes=notes,
            created_by=created_by,
        )

        # ۴. ساخت خطوط سفارش
        for line_data in processed_lines:
            StoreOrderLine.objects.create(
                order=order,
                product_id=line_data['product_id'],
                qty=line_data['qty'],
                unit_price=line_data['unit_price'],
                is_smart_suggestion=line_data['is_smart_suggestion'],
                notes=line_data['notes'],
                created_by=created_by,
            )

        # ۵. ثبت در ApprovalQueue برای تأیید مدیر
        from apps.approval_workflow.services import ApprovalService
        ApprovalService.create_request(
            ref_doc_type='store_order',
            ref_doc_id=order.id,
            requested_by_id=created_by.id if created_by else None,
            priority='medium',
            notes=f'سفارش فروشگاه: {order.order_no}',
        )

        # ۶. ایجاد اعلان برای مدیر (در فاز ۷ با Push هم ارسال می‌شه)
        StoreNotification.objects.create(
            store_id=store_id,
            title='سفارش جدید ثبت شد',
            body=f'سفارش {order.order_no} با مبلغ {total_amount} ریال ثبت شد و در انتظار تأیید مدیر است.',
            notification_type='order_submitted',
            related_doc_type='store_order',
            related_doc_id=order.id,
        )

        # ۷. به‌روزرسانی اعتبار فعلی فروشگاه
        store.current_credit += total_amount
        store.save(update_fields=['current_credit', 'updated_at'])

        return order

    @staticmethod
    @transaction.atomic
    def cancel_order(*, order_id: int, canceled_by=None) -> StoreOrder:
        """لغو سفارش (در صورت تأیید نشدن)"""
        order = StoreOrder.objects.select_for_update().get(id=order_id)

        if order.status in [StoreOrder.OrderStatus.RECEIVED, StoreOrder.OrderStatus.IN_DELIVERY]:
            raise ValueError('سفارش تحویل‌شده یا در حال تحویل قابل لغو نیست')

        if order.status == StoreOrder.OrderStatus.CANCELED:
            raise ValueError('سفارش قبلاً لغو شده')

        # بازگشت اعتبار به فروشگاه
        store = order.store
        store.current_credit -= order.total_amount
        store.save(update_fields=['current_credit', 'updated_at'])

        order.status = StoreOrder.OrderStatus.CANCELED
        order.save(update_fields=['status', 'updated_at'])

        return order

    @staticmethod
    @transaction.atomic
    def mark_received(*, order_id: int, received_by=None) -> StoreOrder:
        """فروشگاه تأیید می‌کنه که سفارش رو دریافت کرده"""
        order = StoreOrder.objects.select_for_update().get(id=order_id)

        if order.status != StoreOrder.OrderStatus.IN_DELIVERY:
            raise ValueError(
                f'سفارش در وضعیت {order.status} است، قابل دریافت نیست'
            )

        order.status = StoreOrder.OrderStatus.RECEIVED
        order.save(update_fields=['status', 'updated_at'])

        # ایجاد سند فروش قطعی (در فاز ۶ تکمیل می‌شود)
        # SalesService.create_sale(store_id=order.store_id, sales_type='firm', ...)

        # اعلان به مدیر
        StoreNotification.objects.create(
            store=order.store,
            title='سفارش دریافت شد',
            body=f'فروشگاه {order.store.name} تأیید کرد که سفارش {order.order_no} را دریافت کرده است.',
            notification_type='order_received',
            related_doc_type='store_order',
            related_doc_id=order.id,
        )

        return order

    @staticmethod
    def get_catalog(store_id: int):
        """کاتالوگ محصولات با قیمت مناسب برای فروشگاه"""
        store = Store.objects.get(id=store_id)
        products = Product.objects.filter(
            is_active=True,
            deleted_at__isnull=True,
        ).select_related('category').prefetch_related('images')

        catalog = []
        for product in products:
            unit_price = StorePortalService._get_price_for_store(
                product=product, store=store,
            )
            image_url = None
            if product.default_image:
                # در حالت واقعی با request context استفاده می‌شه
                image_url = product.default_image.image.name

            catalog.append({
                'product_id': product.id,
                'code': product.code,
                'name': product.name,
                'unit': product.unit,
                'shelf_life_days': product.shelf_life_days,
                'default_price': str(product.default_price),
                'unit_price': str(unit_price),
                'discount_pct': store.discount_percentage,
                'image_url': image_url,
                'category': product.category.name if product.category else '',
            })

        return catalog

    @staticmethod
    def get_balance(store_id: int) -> dict:
        """مانده حساب و اعتبار فروشگاه"""
        store = Store.objects.get(id=store_id)
        return {
            'store_id': store.id,
            'store_name': store.name,
            'tier': store.tier,
            'credit_limit': str(store.credit_limit),
            'current_credit': str(store.current_credit),
            'available_credit': str(store.available_credit),
            'loyalty_points': store.loyalty_points,
            'discount_pct': store.discount_percentage,
        }

    @staticmethod
    def get_order_history(store_id: int, limit: int = 50):
        """تاریخچه سفارش‌های فروشگاه"""
        orders = StoreOrder.objects.filter(
            store_id=store_id,
            deleted_at__isnull=True,
        ).order_by('-order_date', '-id')[:limit]

        return [
            {
                'id': o.id,
                'order_no': o.order_no,
                'order_date': o.order_date.isoformat(),
                'status': o.status,
                'payment_status': o.payment_status,
                'total_amount': str(o.total_amount),
                'total_qty': str(o.total_qty),
                'expected_delivery': o.expected_delivery.isoformat() if o.expected_delivery else None,
            }
            for o in orders
        ]

    @staticmethod
    def get_notifications(store_id: int, unread_only: bool = False):
        """اعلان‌های فروشگاه"""
        qs = StoreNotification.objects.filter(store_id=store_id)
        if unread_only:
            qs = qs.filter(is_read=False)
        return qs

    @staticmethod
    @transaction.atomic
    def mark_notification_read(*, notification_id: int):
        """علامت‌گذاری اعلان به‌عنوان خوانده‌شده"""
        notification = StoreNotification.objects.get(id=notification_id)
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return notification

    @staticmethod
    def _get_price_for_store(*, product: Product, store: Store) -> Decimal:
        """دریافت قیمت مناسب بر اساس لایه فروشگاه"""
        today = timezone.now().date()
        pricing = PricingRule.objects.filter(
            product=product,
            store_tier=store.tier,
            effective_date__lte=today,
        ).filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gte=today),
            deleted_at__isnull=True,
        ).order_by('-effective_date').first()

        if pricing:
            # اعمال تخفیف لایه
            discount_factor = Decimal(1) - (Decimal(store.discount_percentage) / Decimal(100))
            return pricing.default_price * discount_factor
        return product.default_price

    @staticmethod
    def _generate_order_number() -> str:
        year = timezone.now().year
        count = StoreOrder.objects.count() + 1
        return f'ORD-{year}-{count:06d}'


from django.db import models  # noqa
