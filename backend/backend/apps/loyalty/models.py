"""
Loyalty Models — LoyaltyTier, DiscountRule, ReorderSuggestion
"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class LoyaltyTier(models.Model):
    """تعریف لایه‌های وفاداری"""

    class TierName(models.TextChoices):
        REGULAR = 'regular', _('عادی')
        SILVER = 'silver', _('نقره‌ای')
        GOLD = 'gold', _('طلایی')
        PLATINUM = 'platinum', _('پلاتین')

    name = models.CharField(
        max_length=20,
        choices=TierName.choices,
        unique=True,
        verbose_name=_('نام لایه'),
    )
    min_points = models.PositiveIntegerField(verbose_name=_('حداقل امتیاز'))
    discount_percentage = models.DecimalField(
        max_digits=5, decimal_places=2,
        default=0,
        verbose_name=_('درصد تخفیف'),
    )
    credit_increase_percentage = models.DecimalField(
        max_digits=5, decimal_places=2,
        default=0,
        verbose_name=_('افزایش اعتبار'),
    )
    is_active = models.BooleanField(default=True, verbose_name=_('فعال'))

    class Meta:
        db_table = 'loyalty_tiers'
        verbose_name = _('لایه وفاداری')
        verbose_name_plural = _('لایه‌های وفاداری')
        ordering = ['min_points']

    def __str__(self):
        return f'{self.name} ({self.min_points}+ pts, {self.discount_percentage}% discount)'


class DiscountRule(models.Model):
    """قوانین تخفیف"""

    code = models.CharField(max_length=50, unique=True, verbose_name=_('کد'))
    name = models.CharField(max_length=200, verbose_name=_('نام'))
    discount_percentage = models.DecimalField(
        max_digits=5, decimal_places=2,
        verbose_name=_('درصد تخفیف'),
    )
    applies_to_tier = models.CharField(
        max_length=20, blank=True,
        verbose_name=_('فقط برای لایه'),
    )
    starts_at = models.DateTimeField(verbose_name=_('شروع'))
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name=_('پایان'))
    usage_limit = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_('حد استفاده'),
    )
    usage_count = models.PositiveIntegerField(default=0, verbose_name=_('تعداد استفاده'))
    is_active = models.BooleanField(default=True, verbose_name=_('فعال'))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'discount_rules'
        verbose_name = _('قانون تخفیف')
        verbose_name_plural = _('قوانین تخفیف')
        ordering = ['-starts_at']

    def __str__(self):
        return f'{self.code} - {self.discount_percentage}%'

    @property
    def is_valid(self):
        """آیا این تخفیف الان معتبر است؟"""
        from django.utils import timezone
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        if self.usage_limit and self.usage_count >= self.usage_limit:
            return False
        return True


class ReorderSuggestion(models.Model):
    """پیشنهاد سفارش هوشمند — تولیدشده بر اساس داده‌های فروش"""

    store = models.ForeignKey(
        'partners.Store',
        on_delete=models.CASCADE,
        related_name='reorder_suggestions',
        verbose_name=_('فروشگاه'),
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='reorder_suggestions',
        verbose_name=_('محصول'),
    )
    suggested_qty = models.DecimalField(
        max_digits=14, decimal_places=3,
        verbose_name=_('مقدار پیشنهادی'),
    )
    current_stock = models.DecimalField(
        max_digits=14, decimal_places=3,
        verbose_name=_('موجودی فعلی'),
    )
    daily_rate = models.DecimalField(
        max_digits=14, decimal_places=3,
        verbose_name=_('نرخ فروش روزانه'),
    )
    days_of_stock = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name=_('روز باقی‌مانده'),
    )
    confidence_score = models.DecimalField(
        max_digits=5, decimal_places=2,
        default=0,
        verbose_name=_('امتیاز اعتماد'),
    )
    is_processed = models.BooleanField(
        default=False,
        verbose_name=_('پردازش شده'),
        help_text=_('آیا به سبد سفارش اضافه شد؟'),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'reorder_suggestions'
        verbose_name = _('پیشنهاد سفارش')
        verbose_name_plural = _('پیشنهادهای سفارش')
        ordering = ['-days_of_stock', '-created_at']
        unique_together = ('store', 'product', 'created_at')
        indexes = [
            models.Index(fields=['store', 'is_processed']),
            models.Index(fields=['days_of_stock']),
        ]

    def __str__(self):
        return f'{self.store.name} - {self.product.code} ({self.suggested_qty})'
