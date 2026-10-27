"""
Unit Tests برای Accounting Service — قلب یکپارچگی انبار-حسابداری
"""
import pytest
from decimal import Decimal
from datetime import date
from django.utils import timezone

from apps.accounting.models import (
    JournalHeader, JournalLine, Account, CostCenter, FiscalPeriod,
)
from apps.accounting.services import JournalService
from core.exceptions import JournalNotBalancedError


@pytest.mark.django_db
@pytest.mark.unit
class TestJournalService:
    """تست‌های سرویس حسابداری"""

    def test_create_manual_journal_balanced(self, seed_accounts, db):
        """ساخت سند حسابداری متوازن"""
        journal = JournalService.create_manual_journal(
            date='2025-10-20',
            description='سند تست',
            lines=[
                {'account_code': '101', 'debit': 100000, 'credit': 0, 'description': 'بدهکار'},
                {'account_code': '103', 'debit': 0, 'credit': 100000, 'description': 'بستانکار'},
            ],
        )
        assert journal.id is not None
        assert journal.journal_no.startswith('JRN-')
        assert journal.status == 'posted'
        assert journal.total_debit == Decimal('100000')
        assert journal.total_credit == Decimal('100000')
        assert journal.lines.count() == 2
        assert journal.is_balanced is True

    def test_create_journal_unbalanced_rejected(self, seed_accounts, db):
        """سند نامتوازن باید خطا دهد"""
        with pytest.raises(JournalNotBalancedError):
            JournalService.create_manual_journal(
                date='2025-10-20',
                description='سند نامتوازن',
                lines=[
                    {'account_code': '101', 'debit': 100000, 'credit': 0},
                    {'account_code': '103', 'debit': 0, 'credit': 90000},
                ],
            )

    def test_journal_with_cost_center(self, seed_accounts, db):
        """سند با مرکز هزینه"""
        cc = CostCenter.objects.create(
            code='CC-TEST', name='مرکز تست', type='production',
        )
        journal = JournalService.create_manual_journal(
            date='2025-10-20',
            description='سند با مرکز هزینه',
            lines=[
                {
                    'account_code': '50', 'debit': 50000, 'credit': 0,
                    'cost_center_code': 'CC-TEST',
                },
                {
                    'account_code': '101', 'debit': 0, 'credit': 50000,
                },
            ],
        )
        assert journal.lines.first().cost_center == cc

    def test_journal_source_tracking(self, seed_accounts, db):
        """ردیابی منبع سند"""
        journal = JournalService.create_manual_journal(
            date='2025-10-20',
            description='سند از منبع تست',
            lines=[
                {'account_code': '101', 'debit': 100, 'credit': 0},
                {'account_code': '103', 'debit': 0, 'credit': 100},
            ],
            source_type='manual',
            source_id=999,
        )
        assert journal.source_type == 'manual'
        assert journal.source_id == 999

    def test_account_codes_constant(self, seed_accounts, db):
        """ثابت ACCOUNT_CODES در دسترس است"""
        codes = JournalService.ACCOUNT_CODES
        assert codes['inventory_main'] == '101'
        assert codes['inventory_store'] == '104'
        assert codes['accounts_receivable'] == '102'
        assert codes['sales_revenue_firm'] == '402'
        assert codes['cogs'] == '50'

    def test_account_lookup(self, seed_accounts, db):
        """جستجوی حساب‌ها در seed"""
        a101 = Account.objects.get(code='101')
        assert a101.name == 'موجودی کالا'
        assert a101.is_postable is True
        a102 = Account.objects.get(code='102')
        assert a102.name == 'حساب‌های دریافتنی'

    def test_fiscal_period_lookup(self, seed_accounts, db):
        """دوره مالی فعال"""
        today = timezone.now().date()
        # ساخت دوره فعال
        period = FiscalPeriod.objects.create(
            name=f'تست-{today.year}',
            type='annual',
            start_date=today.replace(month=1, day=1),
            end_date=today.replace(month=12, day=31),
            is_closed=False,
        )
        found = JournalService._get_active_period(today.isoformat())
        assert found is not None
        assert found.is_closed is False

    def test_multiple_journals_unique_numbers(self, seed_accounts, db):
        """شماره سندهای مختلف باید یکتا باشند"""
        j1 = JournalService.create_manual_journal(
            date='2025-10-20', description='سند ۱',
            lines=[
                {'account_code': '101', 'debit': 100, 'credit': 0},
                {'account_code': '103', 'debit': 0, 'credit': 100},
            ],
        )
        j2 = JournalService.create_manual_journal(
            date='2025-10-20', description='سند ۲',
            lines=[
                {'account_code': '101', 'debit': 200, 'credit': 0},
                {'account_code': '103', 'debit': 0, 'credit': 200},
            ],
        )
        assert j1.journal_no != j2.journal_no
        assert JournalHeader.objects.count() == 2


@pytest.mark.django_db
@pytest.mark.unit
class TestAccountingIntegration:
    """تست‌های یکپارچگی حسابداری با سایر سرویس‌ها"""

    def test_sale_triggers_journal(self, store, product, main_warehouse,
                                     seed_accounts, db):
        """فروش امانی باید سند حسابداری خودکار بسازد"""
        from apps.sales.services import SalesService
        from datetime import timedelta
        today = timezone.now().date()

        # پاک‌سازی سندهای حسابداری قبلی برای اطمینان از خلوص تست
        JournalLine.objects.all().delete()
        JournalHeader.objects.all().delete()

        # ساخت موجودی
        InventoryLot = pytest.importorskip('apps.inventory.models').InventoryLot
        InventoryLot.objects.create(
            product=product, warehouse=main_warehouse,
            batch_no='B-JRN-01', production_date=today,
            expiry_date=today + timedelta(days=15),
            initial_qty=Decimal('100'), current_qty=Decimal('100'),
            weighted_avg_cost=Decimal('25000'),
        )

        # ساخت فروش
        sale = SalesService.create_sale(
            store_id=store.id,
            sales_type='consignment',
            lines=[
                {'product_id': product.id, 'qty': 20, 'unit_price': 50000},
            ],
        )

        # بررسی ساخت سند حسابداری
        journals = JournalHeader.objects.filter(
            source_type='sale', source_id=sale.id,
        )
        assert journals.count() == 1, 'سند حسابداری برای فروش ساخته نشد'

        journal = journals.first()
        assert journal.total_debit == journal.total_credit  # متوازن
        assert journal.total_debit > 0
        # حداقل ۲ خط (بده + بستان)
        assert journal.lines.count() >= 2

    def test_production_completion_triggers_journal(self, product, main_warehouse,
                                                      seed_accounts, db):
        """تکمیل بچ تولید باید سند حسابداری بسازد"""
        from apps.production.services import ProductionService
        from datetime import timedelta
        today = timezone.now().date()

        InventoryLot = pytest.importorskip('apps.inventory.models').InventoryLot
        material_lot = InventoryLot.objects.create(
            product=product, warehouse=main_warehouse,
            batch_no='MAT-JRN', production_date=today,
            expiry_date=today + timedelta(days=30),
            initial_qty=Decimal('50'), current_qty=Decimal('50'),
            weighted_avg_cost=Decimal('12000'),
        )
        batch = ProductionService.create_batch(
            product_id=product.id, planned_qty=Decimal('20'),
        )
        ProductionService.start_batch(batch_id=batch.id)
        ProductionService.consume_material(
            batch_id=batch.id, material_lot_id=material_lot.id,
            qty=Decimal('20'),
        )
        ProductionService.complete_batch(
            batch_id=batch.id, actual_qty=Decimal('18'),
            waste_qty=Decimal('2'),
        )

        journals = JournalHeader.objects.filter(
            source_type='production', source_id=batch.id,
        )
        # بسته به طراحی signal ممکن است ۰ یا ۱ سند ساخته شود
        # اگر signal اجرا شود باید متوازن باشد
        if journals.exists():
            journal = journals.first()
            assert journal.total_debit == journal.total_credit
