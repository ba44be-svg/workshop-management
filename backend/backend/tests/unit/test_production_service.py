"""
Unit Tests برای Production Service — بچ تولید
"""
import pytest
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone

from apps.production.models import ProductionBatch, ProductionConsumption, ProductionOutput
from apps.production.services import ProductionService
from apps.inventory.models import InventoryLot, InventoryMovement


@pytest.mark.django_db
@pytest.mark.unit
class TestProductionService:
    """تست‌های سرویس تولید"""

    def test_create_batch(self, product, db):
        """تست پایه: ساخت بچ تولید"""
        batch = ProductionService.create_batch(
            product_id=product.id,
            planned_qty=Decimal('100'),
            notes='تست بچ',
            created_by=None,
        )
        assert batch.id is not None
        assert batch.batch_no.startswith('BATCH-')
        assert batch.status == 'planned'
        assert batch.planned_qty == Decimal('100')
        assert batch.actual_qty == Decimal('0')

    def test_start_batch(self, product, db):
        """شروع بچ"""
        batch = ProductionService.create_batch(
            product_id=product.id,
            planned_qty=Decimal('50'),
        )
        batch = ProductionService.start_batch(batch_id=batch.id)
        assert batch.status == 'in_progress'
        assert batch.start_at is not None

    def test_start_already_started_fails(self, product, db):
        """شروع بچ قبلاً شروع‌شده باید خطا دهد"""
        batch = ProductionService.create_batch(
            product_id=product.id, planned_qty=Decimal('50'),
        )
        ProductionService.start_batch(batch_id=batch.id)
        with pytest.raises(ValueError, match='وضعیت'):
            ProductionService.start_batch(batch_id=batch.id)

    def test_consume_material(self, product, main_warehouse, db):
        """مصرف ماده اولیه"""
        today = timezone.now().date()
        # ساخت لات ماده اولیه
        material_lot = InventoryLot.objects.create(
            product=product, warehouse=main_warehouse,
            batch_no='MAT-001', production_date=today,
            expiry_date=today + timedelta(days=30),
            initial_qty=Decimal('100'), current_qty=Decimal('100'),
            weighted_avg_cost=Decimal('12000'),
        )
        # ساخت بچ
        batch = ProductionService.create_batch(
            product_id=product.id, planned_qty=Decimal('50'),
        )
        ProductionService.start_batch(batch_id=batch.id)
        # مصرف
        consumption = ProductionService.consume_material(
            batch_id=batch.id, material_lot_id=material_lot.id,
            qty=Decimal('30'),
        )
        assert consumption.qty_consumed == Decimal('30')
        assert consumption.cost_at_consumption == Decimal('12000')

        material_lot.refresh_from_db()
        assert material_lot.current_qty == Decimal('70')  # 100 - 30

        # حرکت انبار ثبت شده
        assert InventoryMovement.objects.filter(
            ref_doc_type='production', ref_doc_id=batch.id,
        ).count() == 1

    def test_consume_insufficient_stock(self, product, main_warehouse, db):
        """مصرف بیشتر از موجودی باید خطا دهد"""
        today = timezone.now().date()
        material_lot = InventoryLot.objects.create(
            product=product, warehouse=main_warehouse,
            batch_no='MAT-002', production_date=today,
            expiry_date=today + timedelta(days=30),
            initial_qty=Decimal('10'), current_qty=Decimal('10'),
            weighted_avg_cost=Decimal('12000'),
        )
        batch = ProductionService.create_batch(
            product_id=product.id, planned_qty=Decimal('50'),
        )
        ProductionService.start_batch(batch_id=batch.id)
        with pytest.raises(ValueError, match='موجودی'):
            ProductionService.consume_material(
                batch_id=batch.id, material_lot_id=material_lot.id,
                qty=Decimal('50'),  # بیشتر از 10
            )

    def test_complete_batch_creates_new_lot(self, product, main_warehouse, db):
        """تکمیل بچ باید لات جدید برای محصول نهایی بسازد"""
        today = timezone.now().date()
        # لات ماده اولیه
        material_lot = InventoryLot.objects.create(
            product=product, warehouse=main_warehouse,
            batch_no='MAT-003', production_date=today,
            expiry_date=today + timedelta(days=30),
            initial_qty=Decimal('200'), current_qty=Decimal('200'),
            weighted_avg_cost=Decimal('12000'),
        )
        # بچ
        batch = ProductionService.create_batch(
            product_id=product.id, planned_qty=Decimal('100'),
        )
        ProductionService.start_batch(batch_id=batch.id)
        ProductionService.consume_material(
            batch_id=batch.id, material_lot_id=material_lot.id,
            qty=Decimal('120'),
        )
        # تکمیل
        batch = ProductionService.complete_batch(
            batch_id=batch.id,
            actual_qty=Decimal('90'),
            waste_qty=Decimal('10'),
        )

        assert batch.status == 'completed'
        assert batch.actual_qty == Decimal('90')
        assert batch.waste_qty == Decimal('10')
        assert batch.end_at is not None

        # بهای تمام‌شده = (120 × 12000) / 90 = 16000
        assert batch.weighted_avg_cost == Decimal('16000.0000')

        # لات جدید ساخته شده
        new_lot = InventoryLot.objects.filter(production_batch=batch).first()
        assert new_lot is not None
        assert new_lot.current_qty == Decimal('90')
        assert new_lot.weighted_avg_cost == Decimal('16000.0000')

        # ProductionOutput ثبت شده
        assert ProductionOutput.objects.filter(batch=batch).count() == 1

    def test_cancel_batch(self, product, db):
        """لغو بچ"""
        batch = ProductionService.create_batch(
            product_id=product.id, planned_qty=Decimal('50'),
        )
        batch = ProductionService.cancel_batch(
            batch_id=batch.id, reason='عدم نیاز',
        )
        assert batch.status == 'canceled'

    def test_cancel_completed_fails(self, product, main_warehouse, db):
        """لغو بچ تکمیل‌شده باید خطا دهد"""
        today = timezone.now().date()
        material_lot = InventoryLot.objects.create(
            product=product, warehouse=main_warehouse,
            batch_no='MAT-COMP', production_date=today,
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
        )
        with pytest.raises(ValueError, match='تکمیل‌شده'):
            ProductionService.cancel_batch(batch_id=batch.id)

    def test_efficiency_property(self, product, db):
        """محاسبه راندمان"""
        batch = ProductionService.create_batch(
            product_id=product.id, planned_qty=Decimal('100'),
        )
        assert batch.efficiency == 0  # هنوز تولید نشده
        batch.actual_qty = Decimal('80')
        assert batch.efficiency == 80.0

    def test_production_report(self, product, main_warehouse, db):
        """گزارش تولید"""
        today = timezone.now().date()
        material_lot = InventoryLot.objects.create(
            product=product, warehouse=main_warehouse,
            batch_no='MAT-REP', production_date=today,
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

        report = ProductionService.get_production_report()
        assert report['total_batches'] == 1
        assert report['total_produced'] == '18'
        assert report['total_waste'] == '2'
        assert report['waste_percentage'] == 10.0  # 2 / (18+2) × 100
