"""
Unit Tests برای Dispatch + Transfer Services
"""
import pytest
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone

from apps.dispatch.models import DispatchHeader, DispatchLine
from apps.dispatch.services import DispatchService
from apps.transfers.models import TransferHeader
from apps.transfers.services import TransferService
from apps.inventory.models import InventoryLot, Warehouse, StockBalance
from apps.partners.models import Store, Distributor


@pytest.fixture
def distributor(db):
    return Distributor.objects.create(
        code='D-TEST', name='عامل تست', mobile='09121110999',
    )


@pytest.fixture
def store2(db):
    s = Store.objects.create(
        code='S-TEST-2', name='فروشگاه ۲', sales_model='consignment',
        tier='silver', credit_limit=Decimal('100000000'),
    )
    Warehouse.objects.create(
        code='WH-S2', name='انبار فروشگاه ۲',
        type=Warehouse.WarehouseType.STORE, store=s,
    )
    return s


@pytest.fixture
def dispatch_lot(product, main_warehouse, db):
    """لات آماده برای پخش"""
    today = timezone.now().date()
    return InventoryLot.objects.create(
        product=product, warehouse=main_warehouse,
        batch_no='B-DISP-001', production_date=today,
        expiry_date=today + timedelta(days=15),
        initial_qty=Decimal('100'), current_qty=Decimal('100'),
        weighted_avg_cost=Decimal('25000'),
    )


# ============================================================
# Dispatch Tests
# ============================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestDispatchService:
    """تست‌های سرویس پخش"""

    def test_create_dispatch_basic(self, distributor, store, dispatch_lot, db):
        """ساخت سند پخش پایه"""
        dispatch = DispatchService.create_dispatch(
            distributor_id=distributor.id,
            lines=[
                {
                    'product_id': dispatch_lot.product_id,
                    'lot_id': dispatch_lot.id,
                    'qty': 30,
                    'unit_price': 50000,
                    'dest_store_id': store.id,
                },
            ],
        )
        assert dispatch.id is not None
        assert dispatch.dispatch_no.startswith('DISP-')
        assert dispatch.status == 'pending'
        assert dispatch.total_qty == Decimal('30')
        assert dispatch.total_amount == Decimal('1500000')  # 30 × 50000

    def test_dispatch_transfers_lot_to_store(self, distributor, store, dispatch_lot, db):
        """پخش باید لات را به انبار فروشگاه منتقل کند"""
        dispatch = DispatchService.create_dispatch(
            distributor_id=distributor.id,
            lines=[
                {
                    'product_id': dispatch_lot.product_id,
                    'lot_id': dispatch_lot.id,
                    'qty': 50,
                    'unit_price': 50000,
                    'dest_store_id': store.id,
                },
            ],
        )
        # لات در انبار اصلی کاهش یافته
        dispatch_lot.refresh_from_db()
        assert dispatch_lot.current_qty == Decimal('50')  # 100 - 50

        # لات در انبار فروشگاه ساخته شده
        store_wh = Warehouse.objects.get(store_id=store.id, type='store')
        store_lot = InventoryLot.objects.filter(
            product_id=dispatch_lot.product_id, warehouse=store_wh,
        ).first()
        assert store_lot is not None
        assert store_lot.current_qty == Decimal('50')

    def test_dispatch_status_transitions(self, distributor, store, dispatch_lot, db):
        """تغییر وضعیت‌های پخش: pending → in_delivery → arrived"""
        dispatch = DispatchService.create_dispatch(
            distributor_id=distributor.id,
            lines=[
                {
                    'product_id': dispatch_lot.product_id,
                    'lot_id': dispatch_lot.id,
                    'qty': 30,
                    'unit_price': 50000,
                    'dest_store_id': store.id,
                },
            ],
        )
        assert dispatch.status == 'pending'

        DispatchService.start_delivery(dispatch_id=dispatch.id)
        dispatch.refresh_from_db()
        assert dispatch.status == 'in_delivery'

        DispatchService.mark_arrived(dispatch_id=dispatch.id)
        dispatch.refresh_from_db()
        assert dispatch.status == 'arrived'

    def test_dispatch_cancel_after_arrived_fails(self, distributor, store, dispatch_lot, db):
        """لغو پخش بعد از تحویل نباید مجاز باشد"""
        dispatch = DispatchService.create_dispatch(
            distributor_id=distributor.id,
            lines=[
                {
                    'product_id': dispatch_lot.product_id,
                    'lot_id': dispatch_lot.id,
                    'qty': 30,
                    'unit_price': 50000,
                    'dest_store_id': store.id,
                },
            ],
        )
        DispatchService.start_delivery(dispatch_id=dispatch.id)
        DispatchService.mark_arrived(dispatch_id=dispatch.id)

        with pytest.raises(ValueError, match='تحویل‌شده'):
            DispatchService.cancel_dispatch(dispatch_id=dispatch.id)


# ============================================================
# Transfer Tests
# ============================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestTransferService:
    """تست‌های سرویس انتقال بین فروشگاه‌ها"""

    def test_create_transfer_basic(self, store, store2, dispatch_lot, db):
        """ساخت درخواست انتقال"""
        # لات در انبار فروشگاه ۱ بساز (انبار store در conftest ساخته شده)
        store1_wh = Warehouse.objects.get(store_id=store.id, type='store')
        today = timezone.now().date()
        lot_in_store1 = InventoryLot.objects.create(
            product=dispatch_lot.product, warehouse=store1_wh,
            batch_no='B-TR-01', production_date=today,
            expiry_date=today + timedelta(days=15),
            initial_qty=Decimal('50'), current_qty=Decimal('50'),
            weighted_avg_cost=Decimal('25000'),
        )

        transfer = TransferService.create_transfer(
            from_store_id=store.id,
            to_store_id=store2.id,
            lines=[
                {'product_id': dispatch_lot.product_id, 'lot_id': lot_in_store1.id, 'qty': 20},
            ],
            reason='نیاز فروشگاه ۲',
        )
        assert transfer.id is not None
        assert transfer.transfer_no.startswith('TR-')
        assert transfer.status == 'pending'
        assert transfer.from_store_id == store.id
        assert transfer.to_store_id == store2.id

    def test_transfer_same_store_rejected(self, store, dispatch_lot, db):
        """انتقال به همان فروشگاه باید خطا دهد"""
        store1_wh = Warehouse.objects.get(store_id=store.id, type='store')
        today = timezone.now().date()
        lot_in_store1 = InventoryLot.objects.create(
            product=dispatch_lot.product, warehouse=store1_wh,
            batch_no='B-TR-02', production_date=today,
            expiry_date=today + timedelta(days=15),
            initial_qty=Decimal('50'), current_qty=Decimal('50'),
            weighted_avg_cost=Decimal('25000'),
        )
        with pytest.raises(ValueError, match='مبدأ و مقصد'):
            TransferService.create_transfer(
                from_store_id=store.id,
                to_store_id=store.id,  # همان فروشگاه
                lines=[
                    {'product_id': dispatch_lot.product_id, 'lot_id': lot_in_store1.id, 'qty': 10},
                ],
            )

    def test_transfer_approve_moves_stock(self, store, store2, dispatch_lot, db):
        """تأیید انتقال باید موجودی را بین دو انبار منتقل کند"""
        store1_wh = Warehouse.objects.get(store_id=store.id, type='store')
        today = timezone.now().date()
        lot_in_store1 = InventoryLot.objects.create(
            product=dispatch_lot.product, warehouse=store1_wh,
            batch_no='B-TR-03', production_date=today,
            expiry_date=today + timedelta(days=15),
            initial_qty=Decimal('50'), current_qty=Decimal('50'),
            weighted_avg_cost=Decimal('25000'),
        )

        transfer = TransferService.create_transfer(
            from_store_id=store.id,
            to_store_id=store2.id,
            lines=[
                {'product_id': dispatch_lot.product_id, 'lot_id': lot_in_store1.id, 'qty': 30},
            ],
        )

        TransferService.approve_transfer(transfer_id=transfer.id)

        transfer.refresh_from_db()
        assert transfer.status == 'received'

        lot_in_store1.refresh_from_db()
        assert lot_in_store1.current_qty == Decimal('20')  # 50 - 30

        # انبار فروشگاه ۲ باید لات جدید داشته باشد
        store2_wh = Warehouse.objects.get(store_id=store2.id, type='store')
        lot_in_store2 = InventoryLot.objects.filter(
            product_id=dispatch_lot.product_id, warehouse=store2_wh,
        ).first()
        assert lot_in_store2 is not None
        assert lot_in_store2.current_qty == Decimal('30')

    def test_transfer_reject(self, store, store2, dispatch_lot, db):
        """رد درخواست انتقال"""
        store1_wh = Warehouse.objects.get(store_id=store.id, type='store')
        today = timezone.now().date()
        lot_in_store1 = InventoryLot.objects.create(
            product=dispatch_lot.product, warehouse=store1_wh,
            batch_no='B-TR-04', production_date=today,
            expiry_date=today + timedelta(days=15),
            initial_qty=Decimal('50'), current_qty=Decimal('50'),
            weighted_avg_cost=Decimal('25000'),
        )
        transfer = TransferService.create_transfer(
            from_store_id=store.id,
            to_store_id=store2.id,
            lines=[
                {'product_id': dispatch_lot.product_id, 'lot_id': lot_in_store1.id, 'qty': 10},
            ],
        )
        TransferService.reject_transfer(
            transfer_id=transfer.id, reason='عدم تأیید مدیر',
        )
        transfer.refresh_from_db()
        assert transfer.status == 'rejected'
        # موجودی نباید تغییر کرده باشد
        lot_in_store1.refresh_from_db()
        assert lot_in_store1.current_qty == Decimal('50')

    def test_transfer_insufficient_stock_rejected(self, store, store2, dispatch_lot, db):
        """انتقال بیشتر از موجودی باید خطا دهد"""
        store1_wh = Warehouse.objects.get(store_id=store.id, type='store')
        today = timezone.now().date()
        lot_in_store1 = InventoryLot.objects.create(
            product=dispatch_lot.product, warehouse=store1_wh,
            batch_no='B-TR-05', production_date=today,
            expiry_date=today + timedelta(days=15),
            initial_qty=Decimal('10'), current_qty=Decimal('10'),
            weighted_avg_cost=Decimal('25000'),
        )
        with pytest.raises(ValueError, match='کافی نیست'):
            TransferService.create_transfer(
                from_store_id=store.id,
                to_store_id=store2.id,
                lines=[
                    {'product_id': dispatch_lot.product_id, 'lot_id': lot_in_store1.id, 'qty': 50},
                ],
            )
