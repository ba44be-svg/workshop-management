"""
Workshop Services — خرید مواد اولیه، حواله/برگشت کارگاه
هر سرویس در یک تراکنش atomic اجرا می‌شود و سند حسابداری خودکار می‌سازد.
"""
from decimal import Decimal
from typing import List, Optional
from datetime import timedelta
from django.db import transaction
from django.db.models import F, Sum
from django.utils import timezone

from .models import (
    Contractor, PurchaseHeader, PurchaseLine,
    PurchaseReturn, PurchaseReturnLine,
    WorkshopIssue, WorkshopIssueLine,
    WorkshopReturn, WorkshopReturnLine,
)
from apps.inventory.models import (
    InventoryLot, InventoryMovement, StockBalance, Warehouse,
)
from apps.accounting.models import Account, JournalHeader
from apps.accounting.services import JournalService


class PurchaseService:
    """سرویس خرید مواد اولیه از جانب کارپرداز"""

    @staticmethod
    def generate_purchase_no() -> str:
        """تولید خودکار شماره خرید به فرمت PUR-2026-0001"""
        import datetime as _dt
        year = _dt.date.today().year
        prefix = f'PUR-{year}-'
        last = PurchaseHeader.objects.filter(purchase_no__startswith=prefix).order_by('-id').first()
        if last:
            try:
                seq = int(last.purchase_no.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        return f'{prefix}{seq:04d}'

    @staticmethod
    @transaction.atomic
    def create_purchase(
        *,
        purchase_no: str,
        purchase_date,
        contractor_id: int,
        warehouse_id: int,
        cash_account_id: int,
        lines: List[dict],
        notes: str = '',
        created_by=None,
    ) -> PurchaseHeader:
        """
        ساخت سند خرید مواد اولیه.

        مراحل:
            ۱. ساخت PurchaseHeader
            ۲. برای هر خط: ساخت InventoryLot در انبار مواد اولیه
            ۳. به‌روزرسانی StockBalance (افزایش مقدار + میانگین موزون)
            ۴. ساخت InventoryMovement (type=in, ref=purchase)
            ۵. ساخت JournalHeader خودکار:
                - بدهکار: 101/{warehouse.code}  (موجودی مواد اولیه)
                - بستانکار: cash_account  (نقد/بانک)
            ۶. اتصال journal به purchase
        """
        # ۱. ساخت PurchaseHeader
        purchase = PurchaseHeader.objects.create(
            purchase_no=purchase_no,
            purchase_date=purchase_date,
            contractor_id=contractor_id,
            warehouse_id=warehouse_id,
            cash_account_id=cash_account_id,
            status=PurchaseHeader.PurchaseStatus.POSTED,
            notes=notes,
            created_by=created_by,
        )

        warehouse = Warehouse.objects.select_for_update().get(id=warehouse_id)
        contractor = Contractor.objects.get(id=contractor_id)
        cash_account = Account.objects.get(id=cash_account_id)

        total_amount = Decimal('0')
        total_qty = Decimal('0')

        # ۲-۴. برای هر خط: ساخت لات، حرکت، موجودی تجمیعی
        for idx, line_data in enumerate(lines, start=1):
            # پشتیبانی از محصول جدید: اگه product_id نبود ولی product_name بود، محصول جدید بساز
            product_id = line_data.get('product_id')
            product_name = line_data.get('product_name')
            product_code = line_data.get('product_code')

            if not product_id and product_name:
                # ساخت محصول جدید به‌صورت خودکار
                from apps.products.models import Product, ProductCategory, Unit
                # دسته‌بندی پیش‌فرض (اگه نبود، بساز)
                cat = ProductCategory.objects.first()
                if not cat:
                    cat = ProductCategory.objects.create(code='CAT-GEN', name='کالای عمومی')
                # تولید کد خودکار اگه ارسال نشده
                if not product_code:
                    last_p = Product.objects.order_by('-id').first()
                    next_num = (last_p.id + 1) if last_p else 1
                    product_code = f'RAW-{next_num:04d}'
                # اگه محصول با همین نام/کد وجود داشت، از همان استفاده کن
                existing = Product.objects.filter(code=product_code).first() or Product.objects.filter(name=product_name).first()
                if existing:
                    product_id = existing.id
                else:
                    # واحد پیش‌فرض: عدد (NUM)
                    default_unit = Unit.objects.filter(code='NUM').first() or Unit.objects.first()
                    new_product = Product.objects.create(
                        code=product_code,
                        name=product_name,
                        category=cat,
                        unit=default_unit,
                        shelf_life_days=int(line_data.get('shelf_life_days', 15)),
                        default_price=Decimal(line_data.get('unit_price', '0')),
                        is_active=True,
                    )
                    product_id = new_product.id
                    # واحد محصول اگر ارسال شده و متفاوت از پیش‌فرض
                    unit_id = line_data.get('unit_id')
                    if unit_id:
                        try:
                            u = Unit.objects.get(id=unit_id)
                            new_product.unit = u
                            new_product.save()
                        except Unit.DoesNotExist:
                            pass
            elif not product_id:
                raise ValueError(f'خط {idx}: محصول مشخص نشده (نه product_id و نه product_name)')

            qty = Decimal(line_data['qty'])
            unit_price = Decimal(line_data['unit_price'])
            unit_cost = unit_price  # برای خرید، بهای تمام‌شده = قیمت خرید
            shelf_life_days = int(line_data.get('shelf_life_days', 15))

            # محاسبه تاریخ انقضا — از ورودی کاربر استفاده کن اگر ارسال شده
            from datetime import date as _date
            if isinstance(purchase_date, _date):
                pdate = purchase_date
            else:
                pdate = purchase_date
            # اگر کاربر expiry_date ارسال کرده، از همان استفاده کن؛ وگرنه از shelf_life_days
            user_expiry = line_data.get('expiry_date')
            if user_expiry:
                expiry_date = user_expiry if isinstance(user_expiry, _date) else _date.fromisoformat(str(user_expiry))
            else:
                expiry_date = pdate + timedelta(days=shelf_life_days)
            # شماره لات — از ورودی کاربر استفاده کن اگر ارسال شده
            user_lot_no = line_data.get('lot_no')
            lot_no = user_lot_no if user_lot_no else f'PUR-{purchase.id}-{idx}'

            # ۲. ساخت InventoryLot
            lot = InventoryLot.objects.create(
                product_id=product_id,
                warehouse=warehouse,
                batch_no=lot_no,
                production_date=pdate,
                expiry_date=expiry_date,
                initial_qty=qty,
                current_qty=qty,
                weighted_avg_cost=unit_cost,
                status=InventoryLot.LotStatus.ACTIVE,
                created_by=created_by,
            )

            line_total = qty * unit_price
            # ساخت PurchaseLine
            PurchaseLine.objects.create(
                purchase=purchase,
                product_id=product_id,
                qty=qty,
                unit_price=unit_price,
                unit_cost=unit_cost,
                shelf_life_days=shelf_life_days,
                expiry_date=expiry_date,
                lot_no=lot_no,
                line_total=line_total,
                created_by=created_by,
            )

            # ۳. به‌روزرسانی StockBalance (افزایش مقدار + محاسبه میانگین موزون)
            PurchaseService._update_stock_balance_purchase(
                product_id=product_id,
                warehouse_id=warehouse.id,
                qty_in=qty,
                unit_cost=unit_cost,
                last_lot_id=lot.id,
            )

            # ۴. ساخت InventoryMovement (ورود به انبار مواد اولیه)
            InventoryMovement.objects.create(
                lot=lot,
                product_id=product_id,
                warehouse_id=warehouse.id,
                movement_type=InventoryMovement.MovementType.IN,
                qty=qty,
                unit_cost=unit_cost,
                ref_doc_type='purchase',
                ref_doc_id=purchase.id,
                created_by=created_by,
            )

            total_amount += line_total
            total_qty += qty

        # به‌روزرسانی مجموع‌های purchase
        purchase.total_amount = total_amount
        purchase.total_qty = total_qty
        purchase.save(update_fields=['total_amount', 'total_qty', 'updated_at'])

        # ۵. ساخت JournalHeader خودکار
        # تفصیلی موجودی مواد اولیه: 101/{warehouse.code}
        inventory_detail = JournalService.get_or_create_detail_account(
            parent_code=JournalService.ACCOUNT_CODES['inventory_raw'],
            child_code=warehouse.code,
            name=f'موجودی مواد اولیه - {warehouse.name}',
            acc_type='asset',
            description=f'تفصیلی مواد اولیه انبار {warehouse.code}',
            created_by=created_by,
        )

        journal_lines = [
            {
                'account_code': inventory_detail.code,
                'debit': total_amount,
                'credit': 0,
                'description': f'ورود مواد اولیه - خرید {purchase.purchase_no} (انبار {warehouse.code})',
                'ref_doc_type': 'purchase',
                'ref_doc_id': purchase.id,
            },
            {
                'account_code': cash_account.code,
                'debit': 0,
                'credit': total_amount,
                'description': f'پرداخت نقدی خرید {purchase.purchase_no} (کارپرداز {contractor.code})',
                'ref_doc_type': 'purchase',
                'ref_doc_id': purchase.id,
            },
        ]

        journal = JournalService.create_manual_journal(
            date=purchase.purchase_date,
            description=f'سند خودکار خرید مواد اولیه {purchase.purchase_no} - کارپرداز {contractor.code}',
            lines=journal_lines,
            source_type='purchase',
            source_id=purchase.id,
            created_by=created_by,
        )

        purchase.journal = journal
        purchase.save(update_fields=['journal', 'updated_at'])

        # ارسال سیگنال (برای слушать‌های آتی)
        from .signals import purchase_posted
        purchase_posted.send(sender=PurchaseHeader, instance=purchase, created=True)

        return purchase

    @staticmethod
    def _update_stock_balance_purchase(*, product_id, warehouse_id, qty_in, unit_cost, last_lot_id=None):
        """به‌روزرسانی StockBalance با محاسبه میانگین موزون جدید."""
        from django.db.models import F
        stock, created = StockBalance.objects.select_for_update().get_or_create(
            product_id=product_id,
            warehouse_id=warehouse_id,
            defaults={
                'total_qty': qty_in,
                'total_value': qty_in * unit_cost,
                'last_lot_id': last_lot_id,
            },
        )
        if not created:
            existing_qty = stock.total_qty or Decimal('0')
            existing_value = stock.total_value or Decimal('0')
            new_qty = existing_qty + qty_in
            new_value = existing_value + (qty_in * unit_cost)
            stock.total_qty = new_qty
            stock.total_value = new_value
            stock.last_lot_id = last_lot_id
            stock.save(update_fields=['total_qty', 'total_value', 'last_lot_id', 'updated_at'])


class WorkshopService:
    """سرویس حواله و برگشت کارگاه"""

    @staticmethod
    @transaction.atomic
    def create_issue(
        *,
        issue_no: str,
        issue_date,
        from_warehouse_id: int,
        to_warehouse_id: int,
        lines: List[dict],
        contractor_id: Optional[int] = None,
        employee_id: Optional[int] = None,
        production_batch_id: Optional[int] = None,
        notes: str = '',
        created_by=None,
    ) -> WorkshopIssue:
        """
        ساخت حواله کارگاه.

        مراحل:
            ۱. ساخت WorkshopIssue
            ۲. برای هر خط: FEFO تخصیص لات از انبار مواد اولیه
            ۳. کاهش موجودی لات در from_warehouse، افزایش در to_warehouse
            ۴. ساخت InventoryMovement (خروج از from_warehouse، ورود به to_warehouse)
            ۵. ساخت JournalHeader:
                - بدهکار: 140/{contractor.code}  (کالای نزد کارپرداز)
                - بستانکار: 101/{from_warehouse.code}  (موجودی مواد اولیه)
        """
        from .models import Employee

        # Resolve contractor: explicit contractor_id > employee.workshop.contractor > None
        contractor = None
        employee = None
        if employee_id:
            try:
                employee = Employee.objects.select_related(
                    'workshop', 'workshop__contractor',
                ).get(id=employee_id)
            except Employee.DoesNotExist:
                raise ValueError(f'کارکنان با شناسه {employee_id} یافت نشد.')
            if not contractor_id and employee.workshop_id:
                contractor_id = (
                    employee.workshop.contractor_id
                    if employee.workshop else None
                )
        if contractor_id:
            try:
                contractor = Contractor.objects.get(id=contractor_id)
            except Contractor.DoesNotExist:
                raise ValueError(f'کارپرداز با شناسه {contractor_id} یافت نشد.')

        # ۱. ساخت WorkshopIssue
        issue = WorkshopIssue.objects.create(
            issue_no=issue_no,
            issue_date=issue_date,
            contractor=contractor,
            employee=employee,
            from_warehouse_id=from_warehouse_id,
            to_warehouse_id=to_warehouse_id,
            production_batch_id=production_batch_id,
            status=WorkshopIssue.IssueStatus.POSTED,
            notes=notes,
            created_by=created_by,
        )

        from_wh = Warehouse.objects.get(id=from_warehouse_id)
        to_wh = Warehouse.objects.get(id=to_warehouse_id)

        total_qty = Decimal('0')
        total_value = Decimal('0')

        for line_data in lines:
            product_id = line_data['product_id']
            qty_needed = Decimal(line_data['qty'])

            # ۲. تخصیص FEFO از from_warehouse
            lots_qs = InventoryLot.objects.select_for_update().filter(
                product_id=product_id,
                warehouse_id=from_warehouse_id,
                current_qty__gt=0,
                status=InventoryLot.LotStatus.ACTIVE,
                expiry_date__gt=issue_date,
                deleted_at__isnull=True,
            ).order_by('expiry_date', 'production_date')

            lots = list(lots_qs)
            remaining = qty_needed
            allocated = []

            for lot in lots:
                if remaining <= 0:
                    break
                take = min(lot.current_qty, remaining)
                allocated.append((lot, take))
                remaining -= take

            if remaining > 0:
                available = sum(l.current_qty for l in lots)
                raise ValueError(
                    f'موجودی کافی نیست برای محصول {product_id} در انبار {from_wh.code}. '
                    f'موجودی: {available}، موردنیاز: {qty_needed}'
                )

            for lot, take in allocated:
                # ۳. کاهش from_warehouse lot
                lot.current_qty -= take
                lot.save(update_fields=['current_qty', 'updated_at'])
                unit_cost = lot.weighted_avg_cost or Decimal('0')

                # ساخت WorkshopIssueLine
                WorkshopIssueLine.objects.create(
                    issue=issue,
                    product_id=product_id,
                    lot=lot,
                    qty=take,
                    unit_cost=unit_cost,
                    line_total=take * unit_cost,
                    created_by=created_by,
                )

                # ۴. حرکت خروج از from_warehouse
                InventoryMovement.objects.create(
                    lot=lot,
                    product_id=product_id,
                    warehouse_id=from_warehouse_id,
                    movement_type=InventoryMovement.MovementType.TRANSFER,
                    qty=-take,
                    unit_cost=unit_cost,
                    ref_doc_type='workshop_issue',
                    ref_doc_id=issue.id,
                    created_by=created_by,
                )

                # کاهش StockBalance from_warehouse
                WorkshopService._update_stock_balance(
                    product_id=product_id,
                    warehouse_id=from_warehouse_id,
                    qty_change=-take,
                    value_change=-take * unit_cost,
                    last_lot_id=lot.id,
                )

                # افزایش to_warehouse lot (get_or_create با همان batch_no)
                to_lot, _ = InventoryLot.objects.get_or_create(
                    product_id=product_id,
                    warehouse=to_wh,
                    batch_no=lot.batch_no,
                    defaults={
                        'production_date': lot.production_date,
                        'expiry_date': lot.expiry_date,
                        'initial_qty': Decimal('0'),
                        'current_qty': Decimal('0'),
                        'weighted_avg_cost': lot.weighted_avg_cost,
                        'status': InventoryLot.LotStatus.ACTIVE,
                        'production_batch_id': lot.production_batch_id,
                        'created_by': created_by,
                    },
                )
                to_lot.current_qty += take
                to_lot.save(update_fields=['current_qty', 'updated_at'])

                # حرکت ورود به to_warehouse
                InventoryMovement.objects.create(
                    lot=to_lot,
                    product_id=product_id,
                    warehouse_id=to_warehouse_id,
                    movement_type=InventoryMovement.MovementType.TRANSFER,
                    qty=take,
                    unit_cost=unit_cost,
                    ref_doc_type='workshop_issue',
                    ref_doc_id=issue.id,
                    created_by=created_by,
                )

                # افزایش StockBalance to_warehouse
                WorkshopService._update_stock_balance(
                    product_id=product_id,
                    warehouse_id=to_warehouse_id,
                    qty_change=take,
                    value_change=take * unit_cost,
                    last_lot_id=to_lot.id,
                )

                total_qty += take
                total_value += take * unit_cost

        # به‌روزرسانی مجموع‌های issue
        issue.total_qty = total_qty
        issue.total_value = total_value
        issue.save(update_fields=['total_qty', 'total_value', 'updated_at'])

        # ۵. سند حسابداری خودکار (نیاز به contractor دارد؛ اگر نبود، از ثبت سند صرف‌نظر می‌کنیم)
        if contractor is not None:
            # تفصیلی کالای نزد کارپرداز: 140/{contractor.code}
            workshop_account = contractor.detail_account
            if workshop_account is None:
                # اگر signal به هر دلیلی کار نکرد، اینجا هم می‌سازیم
                workshop_account = JournalService.get_or_create_detail_account(
                    parent_code=JournalService.ACCOUNT_CODES['workshop_goods'],
                    child_code=contractor.code,
                    name=f'کالای نزد کارپرداز - {contractor.name}',
                    acc_type='asset',
                    description=f'تفصیلی کارپرداز {contractor.code}',
                    created_by=created_by,
                )
                contractor.detail_account = workshop_account
                contractor.save(update_fields=['detail_account', 'updated_at'])

            # تفصیلی موجودی مواد اولیه: 101/{from_warehouse.code}
            inventory_account = JournalService.get_or_create_detail_account(
                parent_code=JournalService.ACCOUNT_CODES['inventory_raw'],
                child_code=from_wh.code,
                name=f'موجودی مواد اولیه - {from_wh.name}',
                acc_type='asset',
                description=f'تفصیلی مواد اولیه انبار {from_wh.code}',
                created_by=created_by,
            )

            journal_lines = [
                {
                    'account_code': workshop_account.code,
                    'debit': total_value,
                    'credit': 0,
                    'description': f'کالای نزد کارپرداز {contractor.code} - حواله {issue.issue_no}',
                    'ref_doc_type': 'workshop_issue',
                    'ref_doc_id': issue.id,
                },
                {
                    'account_code': inventory_account.code,
                    'debit': 0,
                    'credit': total_value,
                    'description': f'خروج مواد از انبار {from_wh.code} - حواله {issue.issue_no}',
                    'ref_doc_type': 'workshop_issue',
                    'ref_doc_id': issue.id,
                },
            ]

            journal = JournalService.create_manual_journal(
                date=issue.issue_date,
                description=f'سند خودکار حواله کارگاه {issue.issue_no} - کارپرداز {contractor.code}',
                lines=journal_lines,
                source_type='workshop_issue',
                source_id=issue.id,
                created_by=created_by,
            )

            issue.journal = journal
            issue.save(update_fields=['journal', 'updated_at'])

        from .signals import issue_posted
        issue_posted.send(sender=WorkshopIssue, instance=issue, created=True)

        return issue

    @staticmethod
    @transaction.atomic
    def create_return(
        *,
        return_no: str,
        return_date,
        issue_id: int,
        lines: List[dict],
        reason: str = '',
        created_by=None,
    ) -> WorkshopReturn:
        """
        ساخت برگشت کارگاه — برگرداندن مواد استفاده‌نشده از کارگاه به انبار مواد اولیه.

        مراحل:
            ۱. ساخت WorkshopReturn
            ۲. برای هر خط: کاهش to_warehouse lot (کارگاه)، افزایش from_warehouse lot (مواد اولیه)
            ۳. ساخت InventoryMovement (خروج از کارگاه، ورود به مواد اولیه)
            ۴. ساخت JournalHeader:
                - بدهکار: 101/{to_warehouse.code}  (موجودی مواد اولیه)
                - بستانکار: 140/{contractor.code}  (کالای نزد کارپرداز)
        """
        issue = WorkshopIssue.objects.get(id=issue_id)
        contractor = issue.contractor
        from_wh = issue.to_warehouse      # کارگاه (مبدأ برگشت)
        to_wh = issue.from_warehouse      # مواد اولیه (مقصد برگشت)

        return_doc = WorkshopReturn.objects.create(
            return_no=return_no,
            return_date=return_date,
            issue=issue,
            contractor=contractor,
            from_warehouse=from_wh,
            to_warehouse=to_wh,
            reason=reason,
            status=WorkshopReturn.ReturnStatus.POSTED,
            created_by=created_by,
        )

        total_qty = Decimal('0')
        total_value = Decimal('0')

        for line_data in lines:
            issue_line_id = line_data['issue_line_id']
            qty = Decimal(line_data['qty'])
            issue_line = WorkshopIssueLine.objects.select_for_update().get(id=issue_line_id)

            # بررسی محدودیت مقدار برگشتی
            already_returned = Decimal('0')
            for rl in issue_line.return_lines.all():
                already_returned += rl.qty
            available_to_return = issue_line.qty - already_returned
            if qty > available_to_return:
                raise ValueError(
                    f'مقدار برگشتی ({qty}) بیشتر از مقدار قابل برگشت ({available_to_return}) است '
                    f'برای خط {issue_line.id}'
                )

            product_id = issue_line.product_id
            workshop_lot = issue_line.lot  # لات در کارگاه
            unit_cost = issue_line.unit_cost or workshop_lot.weighted_avg_cost or Decimal('0')

            # ۲. کاهش to_warehouse lot (کارگاه)
            # پیدا کردن لات متناظر در کارگاه با همان batch_no
            workshop_lot_actual = InventoryLot.objects.select_for_update().filter(
                product_id=product_id,
                warehouse=from_wh,
                batch_no=workshop_lot.batch_no,
            ).first()
            if workshop_lot_actual is None or workshop_lot_actual.current_qty < qty:
                available = workshop_lot_actual.current_qty if workshop_lot_actual else Decimal('0')
                raise ValueError(
                    f'موجودی لات در کارگاه کافی نیست. موجود: {available}، درخواست: {qty}'
                )

            workshop_lot_actual.current_qty -= qty
            workshop_lot_actual.save(update_fields=['current_qty', 'updated_at'])

            # ساخت WorkshopReturnLine
            WorkshopReturnLine.objects.create(
                return_doc=return_doc,
                issue_line=issue_line,
                qty=qty,
                unit_cost=unit_cost,
                line_total=qty * unit_cost,
                created_by=created_by,
            )

            # ۳. حرکت خروج از کارگاه
            InventoryMovement.objects.create(
                lot=workshop_lot_actual,
                product_id=product_id,
                warehouse_id=from_wh.id,
                movement_type=InventoryMovement.MovementType.RETURN,
                qty=-qty,
                unit_cost=unit_cost,
                ref_doc_type='workshop_return',
                ref_doc_id=return_doc.id,
                created_by=created_by,
            )

            # کاهش StockBalance کارگاه
            WorkshopService._update_stock_balance(
                product_id=product_id,
                warehouse_id=from_wh.id,
                qty_change=-qty,
                value_change=-qty * unit_cost,
                last_lot_id=workshop_lot_actual.id,
            )

            # افزایش to_warehouse lot (مواد اولیه) — get_or_create با همان batch_no
            raw_lot, _ = InventoryLot.objects.get_or_create(
                product_id=product_id,
                warehouse=to_wh,
                batch_no=workshop_lot_actual.batch_no,
                defaults={
                    'production_date': workshop_lot_actual.production_date,
                    'expiry_date': workshop_lot_actual.expiry_date,
                    'initial_qty': Decimal('0'),
                    'current_qty': Decimal('0'),
                    'weighted_avg_cost': workshop_lot_actual.weighted_avg_cost,
                    'status': InventoryLot.LotStatus.ACTIVE,
                    'production_batch_id': workshop_lot_actual.production_batch_id,
                    'created_by': created_by,
                },
            )
            raw_lot.current_qty += qty
            raw_lot.save(update_fields=['current_qty', 'updated_at'])

            # حرکت ورود به مواد اولیه
            InventoryMovement.objects.create(
                lot=raw_lot,
                product_id=product_id,
                warehouse_id=to_wh.id,
                movement_type=InventoryMovement.MovementType.RETURN,
                qty=qty,
                unit_cost=unit_cost,
                ref_doc_type='workshop_return',
                ref_doc_id=return_doc.id,
                created_by=created_by,
            )

            # افزایش StockBalance مواد اولیه
            WorkshopService._update_stock_balance(
                product_id=product_id,
                warehouse_id=to_wh.id,
                qty_change=qty,
                value_change=qty * unit_cost,
                last_lot_id=raw_lot.id,
            )

            total_qty += qty
            total_value += qty * unit_cost

        # به‌روزرسانی مجموع‌ها
        return_doc.total_qty = total_qty
        return_doc.total_value = total_value
        return_doc.save(update_fields=['total_qty', 'total_value', 'updated_at'])

        # ۴. سند حسابداری خودکار
        workshop_account = contractor.detail_account
        if workshop_account is None:
            workshop_account = JournalService.get_or_create_detail_account(
                parent_code=JournalService.ACCOUNT_CODES['workshop_goods'],
                child_code=contractor.code,
                name=f'کالای نزد کارپرداز - {contractor.name}',
                acc_type='asset',
                description=f'تفصیلی کارپرداز {contractor.code}',
                created_by=created_by,
            )
            contractor.detail_account = workshop_account
            contractor.save(update_fields=['detail_account', 'updated_at'])

        inventory_account = JournalService.get_or_create_detail_account(
            parent_code=JournalService.ACCOUNT_CODES['inventory_raw'],
            child_code=to_wh.code,
            name=f'موجودی مواد اولیه - {to_wh.name}',
            acc_type='asset',
            description=f'تفصیلی مواد اولیه انبار {to_wh.code}',
            created_by=created_by,
        )

        journal_lines = [
            {
                'account_code': inventory_account.code,
                'debit': total_value,
                'credit': 0,
                'description': f'بازگشت مواد به انبار {to_wh.code} - برگشت {return_doc.return_no}',
                'ref_doc_type': 'workshop_return',
                'ref_doc_id': return_doc.id,
            },
            {
                'account_code': workshop_account.code,
                'debit': 0,
                'credit': total_value,
                'description': f'کاهش کالای نزد کارپرداز {contractor.code} - برگشت {return_doc.return_no}',
                'ref_doc_type': 'workshop_return',
                'ref_doc_id': return_doc.id,
            },
        ]

        journal = JournalService.create_manual_journal(
            date=return_doc.return_date,
            description=f'سند خودکار برگشت کارگاه {return_doc.return_no} - کارپرداز {contractor.code}',
            lines=journal_lines,
            source_type='workshop_return',
            source_id=return_doc.id,
            created_by=created_by,
        )

        return_doc.journal = journal
        return_doc.save(update_fields=['journal', 'updated_at'])

        from .signals import return_posted
        return_posted.send(sender=WorkshopReturn, instance=return_doc, created=True)

        return return_doc

    @staticmethod
    def _update_stock_balance(*, product_id, warehouse_id, qty_change, value_change, last_lot_id=None):
        """به‌روزرسانی موجودی تجمیعی (Upsert)."""
        from django.db.models import F
        stock, created = StockBalance.objects.select_for_update().get_or_create(
            product_id=product_id,
            warehouse_id=warehouse_id,
            defaults={
                'total_qty': qty_change,
                'total_value': value_change,
                'last_lot_id': last_lot_id,
            },
        )
        if not created:
            stock.total_qty = F('total_qty') + qty_change
            stock.total_value = F('total_value') + value_change
            stock.last_lot_id = last_lot_id
            stock.save(update_fields=['total_qty', 'total_value', 'last_lot_id', 'updated_at'])


# ============================================================================
# PurchaseReturnService — برگشت از خرید
# ============================================================================

class PurchaseReturnService:
    """سرویس برگشت از خرید — بازگشت کالا به تأمین‌کننده/کارپرداز"""

    @staticmethod
    def generate_return_no() -> str:
        """تولید خودکار شماره برگشت: PRT-2026-0001"""
        import datetime as _dt
        year = _dt.date.today().year
        prefix = f'PRT-{year}-'
        last = PurchaseReturn.objects.filter(return_no__startswith=prefix).order_by('-id').first()
        if last:
            try:
                seq = int(last.return_no.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        return f'{prefix}{seq:04d}'

    @staticmethod
    @transaction.atomic
    def create_return(
        *,
        return_no: str,
        return_date,
        purchase_id: int,
        lines: List[dict],
        reason: str = '',
        created_by=None,
    ) -> PurchaseReturn:
        """
        ساخت سند برگشت از خرید.

        مراحل:
            ۱. ساخت PurchaseReturn
            ۲. برای هر خط: کاهش موجودی لات، کاهش StockBalance
            ۳. ساخت InventoryMovement (type=out, ref=purchase_return)
            ۴. ساخت JournalHeader خودکار:
                - بدهکار: 103 (نقد/بانک) — بازگشت پول به صندوق
                - بستانکار: 101 (موجودی مواد اولیه) — خروج کالا از انبار
            ۵. اتصال journal به return
        """
        purchase = PurchaseHeader.objects.select_for_update().get(id=purchase_id)
        warehouse = purchase.warehouse
        cash_account = purchase.cash_account
        contractor = purchase.contractor

        # ساخت سند برگشت
        return_doc = PurchaseReturn.objects.create(
            return_no=return_no,
            return_date=return_date,
            purchase=purchase,
            contractor=contractor,
            warehouse=warehouse,
            cash_account=cash_account,
            status=PurchaseReturn.ReturnStatus.POSTED,
            reason=reason,
            created_by=created_by,
        )

        total_amount = Decimal('0')
        total_qty = Decimal('0')

        for line_data in lines:
            purchase_line_id = line_data['purchase_line_id']
            qty = Decimal(line_data['qty'])

            # پیدا کردن خط خرید اصلی
            pl = PurchaseLine.objects.select_for_update().get(id=purchase_line_id)

            # اعتبارسنجی: مقدار برگشتی نباید بیشتر از مقداد خرید باشه
            already_returned = PurchaseReturnLine.objects.filter(
                purchase_line_id=purchase_line_id
            ).aggregate(t=Sum('qty'))['t'] or Decimal('0')
            available = pl.qty - already_returned
            if qty > available:
                raise ValueError(
                    f'مقدار برگشتی ({qty}) بیشتر از موجودی قابل برگشت ({available}) است.'
                )

            # پیدا کردن لات مرتبط
            lot = InventoryLot.objects.select_for_update().filter(
                batch_no=pl.lot_no,
                product=pl.product,
                warehouse=warehouse,
            ).first()
            if not lot:
                raise ValueError(f'لات {pl.lot_no} یافت نشد.')

            if qty > lot.current_qty:
                raise ValueError(
                    f'مقدار برگشتی ({qty}) بیشتر از موجودی لات ({lot.current_qty}) است.'
                )

            # کاهش موجودی لات
            lot.current_qty = F('current_qty') - qty
            lot.save(update_fields=['current_qty', 'updated_at'])

            # کاهش StockBalance
            unit_cost = pl.unit_cost
            value_change = qty * unit_cost
            PurchaseReturnService._decrease_stock_balance(
                product_id=pl.product_id,
                warehouse_id=warehouse.id,
                qty_change=qty,
                value_change=value_change,
                last_lot_id=lot.id,
            )

            # ساخت InventoryMovement (خروج)
            InventoryMovement.objects.create(
                product=pl.product,
                warehouse=warehouse,
                lot=lot,
                movement_type=InventoryMovement.MovementType.OUT,
                qty=qty,
                unit_cost=unit_cost,
                ref_doc_type='purchase_return',
                ref_doc_id=return_doc.id,
                created_by=created_by,
            )

            # ساخت خط برگشت
            line_total = qty * pl.unit_price
            PurchaseReturnLine.objects.create(
                return_doc=return_doc,
                purchase_line=pl,
                product=pl.product,
                lot=lot,
                qty=qty,
                unit_price=pl.unit_price,
                line_total=line_total,
                created_by=created_by,
            )

            total_amount += line_total
            total_qty += qty

        # به‌روزرسانی جمع کل
        return_doc.total_amount = total_amount
        return_doc.total_qty = total_qty
        return_doc.save(update_fields=['total_amount', 'total_qty', 'updated_at'])

        # ساخت سند حسابداری خودکار
        # بدهکار: 103 (نقد/بانک) — بازگشت پول
        # بستانکار: 101 (موجودی مواد اولیه) — خروج کالا
        journal = JournalService.create_manual_journal(
            date=return_date,
            description=f'برگشت از خرید {purchase.purchase_no} - {return_no}',
            lines=[
                {
                    'account_code': JournalService.ACCOUNT_CODES['cash_in_bank'],
                    'debit': total_amount,
                    'credit': 0,
                },
                {
                    'account_code': JournalService.ACCOUNT_CODES.get('inventory_raw', '101'),
                    'debit': 0,
                    'credit': total_amount,
                },
            ],
            created_by=created_by,
        )
        return_doc.journal = journal
        return_doc.save(update_fields=['journal', 'updated_at'])

        return return_doc

    @staticmethod
    def _decrease_stock_balance(*, product_id, warehouse_id, qty_change, value_change, last_lot_id):
        """کاهش موجودی StockBalance"""
        stock, created = StockBalance.objects.get_or_create(
            product_id=product_id,
            warehouse_id=warehouse_id,
            defaults={
                'total_qty': -qty_change,
                'total_value': -value_change,
                'last_lot_id': last_lot_id,
            },
        )
        if not created:
            stock.total_qty = F('total_qty') - qty_change
            stock.total_value = F('total_value') - value_change
            stock.last_lot_id = last_lot_id
            stock.save(update_fields=['total_qty', 'total_value', 'last_lot_id', 'updated_at'])
