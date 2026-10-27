"""
Store Portal Models — StoreOrder, StoreOrderLine, StoreNotification, StoreDashboard
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import BaseModel, AuditedManager
from django.db.models import F


class StoreOrder(BaseModel):
    """سفارش ثبت‌شده توسط فروشگاه از پورتال PWA"""

    objects = AuditedManager()
    all_objects = models.Manager()

    class OrderStatus(models.TextChoices):
        CART = 'cart', _('سبد خرید')
        SUBMITTED = 'submitted', _('ثبت شد')
        UNDER_REVIEW = 'under_review', _('در حال بررسی')
        APPROVED = 'approved', _('تأیید شد')
        REJECTED = 'rejected', _('رد شد')
        IN_DELIVERY = 'in_delivery', _('در حال تحویل')
        RECEIVED = 'received', _('دریافت شد')
        CANCELED = 'canceled', _('لغو شد')

    class PaymentStatus(models.TextChoices):
        INITIATED = 'initiated', _('شروع شده')
        PAID = 'paid', _('پرداخت شد')
        FAILED = 'failed', _('ناموفق')
        VERIFIED = 'verified', _('تأیید شد')
        REFUNDED = 'refunded', _('بازگشت داده شد')

    order_no = models.CharField(max_length=50, unique=True, verbose_name=_('شماره سفارش'))
    store = models.ForeignKey(
        'partners.Store',
        on_delete=models.RESTRICT,
        related_name='orders',
        verbose_name=_('فروشگاه'),
    )
    order_date = models.DateField(verbose_name=_('تاریخ سفارش'))
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.SUBMITTED,
        verbose_name=_('وضعیت'),
    )
    total_amount = models.DecimalField(
        max_digits=18, decimal_places=4,
        default=0,
        verbose_name=_('مبلغ کل'),
    )
    total_qty = models.DecimalField(
        max_digits=14, decimal_places=3,
        default=0,
        verbose_name=_('مجموع تعداد'),
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.INITIATED,
        verbose_name=_('وضعیت پرداخت'),
    )
    expected_delivery = models.DateField(
        null=True, blank=True,
        verbose_name=_('تحویل مورد انتظار'),
    )
    delivery_address = models.TextField(blank=True, verbose_name=_('آدرس تحویل'))
    dispatch = models.ForeignKey(
        'dispatch.DispatchHeader',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='store_orders',
        verbose_name=_('سند پخش'),
    )
    notes = models.TextField(blank=True, verbose_name=_('یادداشت'))

    class Meta:
        db_table = 'store_orders'
        verbose_name = _('سفارش فروشگاه')
        verbose_name_plural = _('سفارش‌های فروشگاه‌ها')
        ordering = ['-order_date', '-id']
        indexes = [
            models.Index(fields=['store', 'order_date']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_status']),
        ]

    def __str__(self):
        return f'{self.order_no} - {self.store.name} - {self.total_amount}'

    @property
    def is_paid(self):
        return self.payment_status == self.PaymentStatus.VERIFIED

    def recalculate_totals(self):
        """محاسبه مجدد مجموع‌ها از روی خطوط"""
        lines = self.lines.all()
        self.total_amount = sum(line.line_total for line in lines) or 0
        self.total_qty = sum(line.qty for line in lines) or 0
        self.save(update_fields=['total_amount', 'total_qty', 'updated_at'])


class StoreOrderLine(BaseModel):
    """اقلام سفارش فروشگاه"""

    order = models.ForeignKey(
        StoreOrder,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name=_('سفارش'),
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.RESTRICT,
        related_name='store_order_lines',
        verbose_name=_('محصول'),
    )
    qty = models.DecimalField(
        max_digits=14, decimal_places=3,
        verbose_name=_('تعداد'),
    )
    unit_price = models.DecimalField(
        max_digits=18, decimal_places=4,
        verbose_name=_('قیمت واحد'),
    )
    is_smart_suggestion = models.BooleanField(
        default=False,
        verbose_name=_('پیشنهاد Smart Reorder'),
        help_text=_('اگر از پیشنهاد هوشمند آمده باشد'),
    )
    notes = models.TextField(blank=True, verbose_name=_('یادداشت'))

    class Meta:
        db_table = 'store_order_lines'
        verbose_name = _('قلم سفارش')
        verbose_name_plural = _('اقلام سفارش')
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['product']),
        ]

    def __str__(self):
        return f'{self.product.code} x {self.qty}'

    @property
    def line_total(self):
        """جمع این قلم"""
        return self.qty * self.unit_price


class StoreNotification(models.Model):
    """اعلان‌های مخصوص هر فروشگاه — نمایش در پورتال PWA"""

    store = models.ForeignKey(
        'partners.Store',
        on_delete=models.CASCADE,
        related_name='portal_notifications',
        verbose_name=_('فروشگاه'),
    )
    title = models.CharField(max_length=200, verbose_name=_('عنوان'))
    body = models.TextField(verbose_name=_('متن'))
    notification_type = models.CharField(
        max_length=50,
        verbose_name=_('نوع'),
        help_text='order_approved, payment_received, expiry_alert, etc.',
    )
    related_doc_type = models.CharField(max_length=50, blank=True, verbose_name=_('نوع سند مرتبط'))
    related_doc_id = models.BigIntegerField(null=True, blank=True, verbose_name=_('شناسه سند مرتبط'))
    is_read = models.BooleanField(default=False, verbose_name=_('خوانده شده'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('زمان'))

    class Meta:
        db_table = 'store_notifications'
        verbose_name = _('اعلان فروشگاه')
        verbose_name_plural = _('اعلان‌های فروشگاه')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['store', 'is_read']),
        ]

    def __str__(self):
        return f'{self.store.name}: {self.title}'


class StoreDashboard(models.Model):
    """داشبورد هر فروشگاه — کش برای نمایش سریع"""

    store = models.OneToOneField(
        'partners.Store',
        on_delete=models.CASCADE,
        related_name='dashboard',
        verbose_name=_('فروشگاه'),
    )
    total_orders = models.PositiveIntegerField(default=0, verbose_name=_('مجموع سفارش‌ها'))
    active_orders = models.PositiveIntegerField(default=0, verbose_name=_('سفارش‌های فعال'))
    total_purchases = models.DecimalField(
        max_digits=18, decimal_places=4,
        default=0,
        verbose_name=_('مجموع خرید'),
    )
    total_paid = models.DecimalField(
        max_digits=18, decimal_places=4,
        default=0,
        verbose_name=_('مجموع پرداخت'),
    )
    balance = models.DecimalField(
        max_digits=18, decimal_places=4,
        default=0,
        verbose_name=_('مانده'),
    )
    loyalty_points = models.PositiveIntegerField(default=0, verbose_name=_('امتیاز وفاداری'))
    unread_notifications = models.PositiveIntegerField(default=0, verbose_name=_('اعلان‌های خوانده‌نشده'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('به‌روزرسانی'))

    class Meta:
        db_table = 'store_dashboards'
        verbose_name = _('داشبورد فروشگاه')
        verbose_name_plural = _('داشبورد فروشگاه‌ها')

    def __str__(self):
        return f'{self.store.name} - Dashboard'

    @classmethod
    def refresh_for_store(cls, store_id):
        """به‌روزرسانی داشبورد یک فروشگاه"""
        from django.db.models import Sum, Count
        from apps.partners.models import LoyaltyPoint

        store_orders = StoreOrder.objects.filter(store_id=store_id)
        active_orders = store_orders.filter(
            status__in=[
                StoreOrder.OrderStatus.SUBMITTED,
                StoreOrder.OrderStatus.UNDER_REVIEW,
                StoreOrder.OrderStatus.APPROVED,
                StoreOrder.OrderStatus.IN_DELIVERY,
            ],
        )
        total_purchases = store_orders.filter(
            status=StoreOrder.OrderStatus.RECEIVED,
        ).aggregate(t=Sum('total_amount'))['t'] or 0

        notifications_count = StoreNotification.objects.filter(
            store_id=store_id, is_read=False,
        ).count()

        loyalty = LoyaltyPoint.objects.filter(store_id=store_id).order_by('-created_at').first()
        loyalty_points = loyalty.new_balance if loyalty else 0

        dashboard, _ = cls.objects.update_or_create(
            store_id=store_id,
            defaults={
                'total_orders': store_orders.count(),
                'active_orders': active_orders.count(),
                'total_purchases': total_purchases,
                'loyalty_points': loyalty_points,
                'unread_notifications': notifications_count,
            },
        )
        return dashboard
