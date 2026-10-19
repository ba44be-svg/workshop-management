"""
Loyalty Services — LoyaltyService + SmartReorderService
"""
from decimal import Decimal
from typing import List
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from django.db.models import Sum
from .models import LoyaltyTier, DiscountRule, ReorderSuggestion
from apps.partners.models import Store, LoyaltyPoint
from apps.sales.models import SalesHeader, SalesLine
from apps.inventory.models import InventoryLot, StockBalance, Warehouse


class LoyaltyService:
    """سرویس وفاداری فروشگاه‌ها"""

    POINTS_PER_100K_RIAL = 1  # ۱ امتیاز به ازای هر ۱۰۰ هزار ریال خرید
    POINTS_PAYMENT_ON_TIME = 5  # امتیاز پرداخت به‌موقع
    POINTS_NO_RETURN = 3  # امتیاز عدم برگشت
    POINTS_TIER_BONUS = {
        'silver': 50,
        'gold': 100,
        'platinum': 200,
    }

    @classmethod
    @transaction.atomic
    def add_points_for_purchase(cls, sale: SalesHeader) -> int:
        """افزودن امتیاز پس از خرید"""
        points = int(sale.total_amount / Decimal(100000)) * cls.POINTS_PER_100K_RIAL

        # اعمال ضریب لایه
        multiplier = cls._get_tier_multiplier(sale.store.tier)
        points = int(points * multiplier)

        cls._add_transaction(
            store=sale.store,
            points_change=points,
            reason='purchase',
            ref_doc_type='sale',
            ref_doc_id=sale.id,
        )
        return points

    @classmethod
    @transaction.atomic
    def add_points_for_payment(cls, store: Store, amount: Decimal) -> int:
        """افزودن امتیاز پس از پرداخت به‌موقع"""
        if cls._is_payment_on_time(store):
            points = cls.POINTS_PAYMENT_ON_TIME
            cls._add_transaction(
                store=store,
                points_change=points,
                reason='payment_ontime',
                ref_doc_type='payment',
                ref_doc_id=None,
            )
            return points
        return 0

    @classmethod
    @transaction.atomic
    def add_points_for_no_return(cls, store: Store) -> int:
        """افزودن امتیاز ماهانه برای عدم برگشت"""
        points = cls.POINTS_NO_RETURN
        cls._add_transaction(
            store=store,
            points_change=points,
            reason='no_return',
            ref_doc_type='monthly_bonus',
            ref_doc_id=None,
        )
        return points

    @classmethod
    @transaction.atomic
    def check_tier_upgrade(cls, store: Store) -> dict:
        """بررسی ارتقاء لایه"""
        old_tier = store.tier
        new_tier = cls._calculate_tier(store.loyalty_points)

        if old_tier != new_tier:
            # اعمال ارتقاء
            store.tier = new_tier
            store.save(update_fields=['tier', 'updated_at'])

            # اعمال افزایش اعتبار
            increase_pct = cls._get_credit_increase(new_tier)
            if increase_pct > 0:
                new_limit = store.credit_limit * (1 + increase_pct / 100)
                store.credit_limit = new_limit
                store.save(update_fields=['credit_limit'])

            # اعطای امتیاز پاداش
            bonus = cls.POINTS_TIER_BONUS.get(new_tier, 0)
            if bonus:
                cls._add_transaction(
                    store=store,
                    points_change=bonus,
                    reason='tier_bonus',
                    ref_doc_type='tier_upgrade',
                    ref_doc_id=store.id,
                )

            # ارسال Push Notification
            from apps.notifications.services import PushService
            try:
                store_owners = store.profiles.filter(user__is_active=True)
                for sp in store_owners:
                    PushService.send_to_user(
                        user_id=sp.user_id,
                        title='ارتقاء لایه',
                        body=f'تبریک! شما به لایه {new_tier} ارتقا یافتید. '
                             f'تخفیف {cls._get_discount_pct(new_tier)}% فعال است.',
                        data={'tier': new_tier},
                    )
            except Exception:
                pass

            return {
                'old_tier': old_tier,
                'new_tier': new_tier,
                'bonus_points': bonus,
                'credit_increase_pct': increase_pct,
            }
        return {'old_tier': old_tier, 'new_tier': new_tier, 'no_change': True}

    @classmethod
    def _add_transaction(cls, *, store: Store, points_change: int, reason: str,
                          ref_doc_type: str, ref_doc_id: int):
        """ثبت یک تراکنش وفاداری"""
        new_balance = store.loyalty_points + points_change

        LoyaltyPoint.objects.create(
            store=store,
            points_change=points_change,
            reason=reason,
            ref_doc_type=ref_doc_type,
            ref_doc_id=ref_doc_id,
            new_balance=new_balance,
        )

        # به‌روزرسانی امتیاز فروشگاه
        store.loyalty_points = new_balance
        store.save(update_fields=['loyalty_points', 'updated_at'])

    @staticmethod
    def _calculate_tier(points: int) -> str:
        """محاسبه لایه بر اساس امتیاز"""
        tiers = LoyaltyTier.objects.filter(is_active=True).order_by('-min_points')
        for tier in tiers:
            if points >= tier.min_points:
                return tier.name
        return 'regular'

    @staticmethod
    def _get_tier_multiplier(tier: str) -> Decimal:
        """ضریب امتیاز بر اساس لایه"""
        return {
            'regular': Decimal('1'),
            'silver': Decimal('1.2'),
            'gold': Decimal('1.5'),
            'platinum': Decimal('2'),
        }.get(tier, Decimal('1'))

    @staticmethod
    def _get_discount_pct(tier: str) -> Decimal:
        """درصد تخفیف لایه"""
        try:
            return LoyaltyTier.objects.get(name=tier).discount_percentage
        except LoyaltyTier.DoesNotExist:
            return Decimal('0')

    @staticmethod
    def _get_credit_increase(tier: str) -> Decimal:
        """درصد افزایش اعتبار"""
        try:
            return LoyaltyTier.objects.get(name=tier).credit_increase_percentage
        except LoyaltyTier.DoesNotExist:
            return Decimal('0')

    @staticmethod
    def _is_payment_on_time(store: Store) -> bool:
        """بررسی پرداخت به‌موقع (ساده)"""
        # اگر در ۷ روز گذشته پرداخت داشته و تأخیر بیش از ۷ روز نبوده
        return True  # Placeholder — در پیاده‌سازی واقعی با مراجعه به payments


class SmartReorderService:
    """سرویس پیشنهاد سفارش هوشمند"""

    DAYS_LOOKBACK = 14  # روزهای گذشته برای محاسبه نرخ فروش
    MIN_DOS_THRESHOLD = 3  # اگر DOS کمتر از ۳ روز، پیشنهاد سفارش

    @classmethod
    def generate_suggestions(cls, *, store_id: int) -> List[dict]:
        """
        تولید پیشنهاد سفارش هوشمند برای فروشگاه.

        الگوریتم:
        ۱. محاسبه نرخ فروش روزانه هر محصول در ۱۴ روز گذشته
        ۲. محاسبه موجودی فعلی محصول در انبار فروشگاه
        ۳. محاسبه Days of Stock (DOS)
        ۴. اگر DOS < ۳ → پیشنهاد سفارش
        ۵. تعداد پیشنهادی = نرخ روزانه × ۷ (یک هفته آینده)
        """
        today = timezone.now().date()
        cutoff_date = today - timedelta(days=cls.DAYS_LOOKBACK)

        # دریافت تمام محصولات فروخته‌شده در ۱۴ روز گذشته
        sales_velocity = (
            SalesLine.objects
            .filter(
                sale__store_id=store_id,
                sale__sale_date__gte=cutoff_date,
                sale__status=SalesHeader.SalesStatus.POSTED,
            )
            .values('product_id')
            .annotate(daily_rate=Sum('qty') / Decimal(cls.DAYS_LOOKBACK))
        )

        suggestions = []
        for item in sales_velocity:
            product_id = item['product_id']
            daily_rate = item['daily_rate']

            if daily_rate <= 0:
                continue

            # محاسبه موجودی فعلی در انبار فروشگاه
            current_stock = cls._get_current_stock(
                product_id=product_id, store_id=store_id,
            )

            # محاسبه DOS
            if daily_rate > 0:
                dos = float(current_stock / daily_rate) if daily_rate > 0 else 999
            else:
                dos = 999

            # اگر DOS کمتر از آستانه، پیشنهاد سفارش
            if dos < cls.MIN_DOS_THRESHOLD:
                # تعداد پیشنهادی: برای ۷ روز آینده
                suggested_qty = max(int(daily_rate * 7), 10)

                # بررسی محدودیت اعتبار فروشگاه
                store = Store.objects.get(id=store_id)
                from apps.products.models import Product, PricingRule
                product = Product.objects.get(id=product_id)

                pricing = PricingRule.objects.filter(
                    product=product,
                    store_tier=store.tier,
                ).order_by('-effective_date').first()
                unit_price = pricing.default_price if pricing else product.default_price

                # اعمال تخفیف لایه
                discount_pct = store.discount_percentage
                final_price = unit_price * (1 - Decimal(discount_pct) / 100)
                total_cost = final_price * suggested_qty

                if total_cost > store.available_credit:
                    # کاهش تعداد بر اساس اعتبار موجود
                    suggested_qty = int(store.available_credit / final_price)
                    if suggested_qty < 5:
                        continue

                # محاسبه امتیاز اعتماد (confidence)
                confidence = cls._calculate_confidence(daily_rate, dos, current_stock)

                # ذخیره در دیتابیس
                suggestion, _ = ReorderSuggestion.objects.update_or_create(
                    store_id=store_id,
                    product_id=product_id,
                    created_at__date=today,
                    defaults={
                        'suggested_qty': suggested_qty,
                        'current_stock': current_stock,
                        'daily_rate': daily_rate,
                        'days_of_stock': Decimal(str(dos)),
                        'confidence_score': confidence,
                        'is_processed': False,
                    },
                )

                suggestions.append({
                    'suggestion_id': suggestion.id,
                    'product_id': product_id,
                    'product_code': product.code,
                    'product_name': product.name,
                    'suggested_qty': suggested_qty,
                    'current_stock': str(current_stock),
                    'daily_rate': str(daily_rate),
                    'days_of_stock': round(dos, 2),
                    'confidence': float(confidence),
                    'unit_price': str(final_price),
                })

        return suggestions

    @staticmethod
    def _get_current_stock(*, product_id, store_id):
        """موجودی فعلی محصول در انبار فروشگاه"""
        try:
            warehouse = Warehouse.objects.get(
                store_id=store_id,
                type=Warehouse.WarehouseType.STORE,
            )
            stock = StockBalance.objects.filter(
                product_id=product_id, warehouse=warehouse,
            ).first()
            return stock.total_qty if stock else Decimal('0')
        except Warehouse.DoesNotExist:
            return Decimal('0')

    @staticmethod
    def _calculate_confidence(daily_rate, dos, current_stock):
        """محاسبه امتیاز اعتماد ۰ تا ۱"""
        # امتیاز بالاتر = اعتماد بیشتر
        # اعداد ساده: نرخ فروش + کمبود موجودی = اعتماد بالا
        try:
            return min(Decimal('1'), Decimal(str(daily_rate)) / 10) * (1 - Decimal(str(dos)) / 10)
        except Exception:
            return Decimal('0.5')
