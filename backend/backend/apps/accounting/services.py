"""
Accounting Service — قلب یکپارچگی انبار-حسابداری
این سرویس اسناد حسابداری را به‌صورت خودکار از تراکنش‌های انبار می‌سازد
"""
from decimal import Decimal
from typing import List, Optional
from django.db import transaction
from django.utils import timezone
from django.db.models import Sum
from .models import (
    JournalHeader, JournalLine, Account, CostCenter, FiscalPeriod,
    JournalTemplate,
)
from core.exceptions import JournalNotBalancedError


class JournalService:
    """سرویس سند حسابداری — قلب یکپارچگی"""

    # کدینگ استاندارد — تفصیلی چند سطحی
    # این کدها به حساب‌های میانی (level 2) یا تفصیلی (level 3) اشاره دارند.
    # برای هر تفصیلی شخصی (level 4) از get_or_create_detail_account استفاده می‌شود.
    ACCOUNT_CODES = {
        'inventory_main': '101',          # موجودی کالا در انبار اصلی (level 3, postable)
        'inventory_raw': '101',           # موجودی مواد اولیه (level 3, postable) — alias
        'inventory_finished': '101F',     # موجودی محصولات (level 3, postable)
        'inventory_store': '104',         # موجودی امانی در فروشگاه (level 3, postable)
        'accounts_receivable': '102',     # حساب‌های دریافتنی از فروشگاه
        'cash_in_bank': '103',            # نقد و بانک (level 3, postable)
        'workshop_goods': '140',          # کالای نزد کارپرداز (level 3, postable)
        'work_in_progress': '141',        # کالای در حال ساخت (level 3, postable)
        'sales_revenue_consignment': '401',  # درآمد فروش امانی
        'sales_revenue_firm': '402',       # درآمد فروش قطعی
        'cogs': '50',                      # بهای تمام‌شده فروش
        'production_waste': '51',          # ضایعات تولید
        'distribution_cost': '52',         # هزینه‌های پخش
    }

    @staticmethod
    def get_or_create_detail_account(
        *,
        parent_code: str,
        child_code: str,
        name: str,
        acc_type: str = 'asset',
        description: str = '',
        created_by=None,
    ) -> 'Account':
        """
        یافتن یا ساخت حساب تفصیلی (level 4) تحت یک والد میانی/تفصیلی.
        کد نهایی: parent_code + '/' + child_code
        مثال: parent_code='140', child_code='C001' → '140/C001'
        """
        parent = Account.objects.filter(code=parent_code).first()
        if parent is None:
            # اگر والد موجود نبود، خودمان آن را تحت یک فرض کلی ('10' یا '4' یا '5')
            # در سطح ۳ ایجاد نمی‌کنیم — باید از قبل در seed ساخته شده باشد.
            raise ValueError(f'حساب والد با کد {parent_code} یافت نشد')

        full_code = f'{parent_code}/{child_code}'
        account, created = Account.objects.get_or_create(
            code=full_code,
            defaults={
                'name': name,
                'type': acc_type,
                'parent': parent,
                'is_active': True,
                'is_postable': True,
                'description': description or f'تفصیلی {name}',
                'created_by': created_by,
            },
        )
        # اگر والد هنوز postable=True شده و سطح < 3 دارد، اصلاح کن
        if parent.level < 3 and parent.is_postable:
            parent.is_postable = False
            parent.save(update_fields=['is_postable', 'updated_at'])
        return account

    @staticmethod
    @transaction.atomic
    def create_manual_journal(
        *,
        date: str,
        description: str,
        lines: List[dict],
        created_by=None,
        source_type: str = 'manual',
        source_id: Optional[int] = None,
    ) -> JournalHeader:
        """
        ساخت سند دستی حسابداری.

        خطوط ورودی:
            [{'account_code': '101', 'debit': 100000, 'credit': 0, 'description': '...'}, ...]
        """
        # بررسی توازن قبل از ساخت
        total_debit = sum(Decimal(l.get('debit', 0)) for l in lines)
        total_credit = sum(Decimal(l.get('credit', 0)) for l in lines)

        if total_debit != total_credit:
            raise JournalNotBalancedError(
                f'سند نامتوازن: بدهکار={total_debit}، بستانکار={total_credit}'
            )

        # یافتن دوره مالی فعال
        period = JournalService._get_active_period(date)

        # ساخت Header
        journal = JournalHeader.objects.create(
            journal_no=JournalService._generate_journal_number(),
            date=date,
            source_type=source_type,
            source_id=source_id,
            total_debit=total_debit,
            total_credit=total_credit,
            status=JournalHeader.JournalStatus.POSTED,
            period=period,
            description=description,
            created_by=created_by,
        )

        # ساخت Lines
        for line_data in lines:
            account = Account.objects.get(code=line_data['account_code'])

            cost_center = None
            if line_data.get('cost_center_code'):
                cost_center = CostCenter.objects.get(code=line_data['cost_center_code'])

            JournalLine.objects.create(
                journal=journal,
                account=account,
                cost_center=cost_center,
                debit=Decimal(line_data.get('debit', 0)),
                credit=Decimal(line_data.get('credit', 0)),
                description=line_data.get('description', ''),
                ref_doc_type=line_data.get('ref_doc_type', ''),
                ref_doc_id=line_data.get('ref_doc_id'),
            )

        return journal

    @staticmethod
    @transaction.atomic
    def create_sale_journal(sale) -> JournalHeader:
        """
        ساخت سند حسابداری خودکار از روی سند فروش.

        برای فروش امانی:
            بدهکار: موجودی امانی فروشگاه (104)
            بستانکار: موجودی انبار اصلی (101)
        برای فروش قطعی:
            بدهکار: حساب‌های دریافتنی از فروشگاه (102)
            بستانکار: درآمد فروش (402) + موجودی کالا (101)
        """
        lines = []
        total_amount = sale.total_amount
        total_cost = sale.total_cost

        if sale.sales_type == 'consignment':
            # انتقال موجودی از انبار اصلی به انبار امانی فروشگاه
            lines.append({
                'account_code': JournalService.ACCOUNT_CODES['inventory_store'],
                'debit': total_cost,
                'credit': 0,
                'description': f'موجودی امانی - فروش {sale.sale_no}',
                'ref_doc_type': 'sale',
                'ref_doc_id': sale.id,
            })
            lines.append({
                'account_code': JournalService.ACCOUNT_CODES['inventory_main'],
                'debit': 0,
                'credit': total_cost,
                'description': f'خروج از انبار - فروش {sale.sale_no}',
                'ref_doc_type': 'sale',
                'ref_doc_id': sale.id,
            })
        elif sale.sales_type == 'firm':
            # فروش قطعی: ثبت درآمد و خروج موجودی
            lines.append({
                'account_code': JournalService.ACCOUNT_CODES['accounts_receivable'],
                'debit': total_amount,
                'credit': 0,
                'description': f'طلب از فروشگاه - فروش {sale.sale_no}',
                'ref_doc_type': 'sale',
                'ref_doc_id': sale.id,
            })
            lines.append({
                'account_code': JournalService.ACCOUNT_CODES['sales_revenue_firm'],
                'debit': 0,
                'credit': total_amount,
                'description': f'درآمد فروش - {sale.sale_no}',
                'ref_doc_type': 'sale',
                'ref_doc_id': sale.id,
            })
            # خروج موجودی به بهای تمام‌شده
            lines.append({
                'account_code': JournalService.ACCOUNT_CODES['cogs'],
                'debit': total_cost,
                'credit': 0,
                'description': f'بهای تمام‌شده فروش - {sale.sale_no}',
                'ref_doc_type': 'sale',
                'ref_doc_id': sale.id,
            })
            lines.append({
                'account_code': JournalService.ACCOUNT_CODES['inventory_main'],
                'debit': 0,
                'credit': total_cost,
                'description': f'خروج موجودی - {sale.sale_no}',
                'ref_doc_type': 'sale',
                'ref_doc_id': sale.id,
            })

        journal = JournalService.create_manual_journal(
            date=sale.sale_date,
            description=f'سند خودکار فروش {sale.sale_no}',
            lines=lines,
            source_type='sale',
            source_id=sale.id,
            created_by=sale.created_by,
        )

        # به‌روزرسانی FK در سند فروش
        sale.journal = journal
        sale.save(update_fields=['journal', 'updated_at'])

        return journal

    @staticmethod
    @transaction.atomic
    def create_return_journal(return_header) -> JournalHeader:
        """ساخت سند معکوس برای برگشت از فروشگاه"""
        sale = return_header.original_sale

        if sale and sale.journal:
            # معکوس کردن سند فروش اصلی
            lines = []
            for orig_line in sale.journal.lines.all():
                lines.append({
                    'account_code': orig_line.account.code,
                    'debit': orig_line.credit,
                    'credit': orig_line.debit,
                    'description': f'برگشت - {return_header.return_no}',
                    'ref_doc_type': 'return',
                    'ref_doc_id': return_header.id,
                })

            journal = JournalService.create_manual_journal(
                date=return_header.return_date,
                description=f'سند برگشت {return_header.return_no}',
                lines=lines,
                source_type='return',
                source_id=return_header.id,
                created_by=return_header.created_by,
            )

            return_header.journal = journal
            return_header.save(update_fields=['journal', 'updated_at'])
            return journal

        return None

    @staticmethod
    @transaction.atomic
    def create_payment_journal(payment_tx) -> JournalHeader:
        """
        ساخت سند حسابداری برای پرداخت آنلاین.
            بدهکار: نقد و بانک (103)
            بستانکار: حساب‌های دریافتنی از فروشگاه (102)
        """
        lines = [
            {
                'account_code': JournalService.ACCOUNT_CODES['cash_in_bank'],
                'debit': payment_tx.amount,
                'credit': 0,
                'description': f'دریافت آنلاین - {payment_tx.transaction_no}',
                'ref_doc_type': 'payment',
                'ref_doc_id': payment_tx.id,
            },
            {
                'account_code': JournalService.ACCOUNT_CODES['accounts_receivable'],
                'debit': 0,
                'credit': payment_tx.amount,
                'description': f'تسویه فروشگاه - {payment_tx.transaction_no}',
                'ref_doc_type': 'payment',
                'ref_doc_id': payment_tx.id,
            },
        ]

        journal = JournalService.create_manual_journal(
            date=payment_tx.paid_at.date() if payment_tx.paid_at else timezone.now().date(),
            description=f'پرداخت آنلاین - {payment_tx.transaction_no}',
            lines=lines,
            source_type='payment',
            source_id=payment_tx.id,
            created_by=payment_tx.created_by,
        )

        payment_tx.journal = journal
        payment_tx.save(update_fields=['journal'])

        return journal

    @staticmethod
    @transaction.atomic
    def reverse_journal(*, journal_id: int, reason: str = '', reversed_by=None):
        """معکوس کردن یک سند — ساخت سند معکوس"""
        original = JournalHeader.objects.get(id=journal_id)

        # ساخت سند معکوس
        lines = []
        for orig_line in original.lines.all():
            lines.append({
                'account_code': orig_line.account.code,
                'debit': orig_line.credit,  # برعکس
                'credit': orig_line.debit,  # برعکس
                'description': f'معکوس - {reason}',
                'ref_doc_type': 'journal_reverse',
                'ref_doc_id': original.id,
            })

        reversal = JournalService.create_manual_journal(
            date=timezone.now().date(),
            description=f'سند معکوس {original.journal_no} - {reason}',
            lines=lines,
            source_type='manual',
            created_by=reversed_by,
        )

        original.status = JournalHeader.JournalStatus.REVERSED
        original.reversed_by_journal = reversal
        original.save(update_fields=['status', 'reversed_by_journal', 'updated_at'])

        return reversal

    @staticmethod
    def get_trial_balance(as_of_date=None):
        """تراز آزمایشی تا تاریخ"""
        if as_of_date is None:
            as_of_date = timezone.now().date()

        accounts = Account.objects.filter(is_postable=True, deleted_at__isnull=True)
        result = []
        for account in accounts:
            lines = JournalLine.objects.filter(
                account=account,
                journal__date__lte=as_of_date,
                journal__status='posted',
            )
            debit = lines.aggregate(t=Sum('debit'))['t'] or Decimal('0')
            credit = lines.aggregate(t=Sum('credit'))['t'] or Decimal('0')
            balance = debit - credit
            result.append({
                'code': account.code,
                'name': account.name,
                'type': account.type,
                'debit': str(debit),
                'credit': str(credit),
                'balance': str(balance),
            })
        return result

    @staticmethod
    def get_profit_loss(date_from=None, date_to=None, cost_center_id=None):
        """گزارش سود و زیان"""
        if date_to is None:
            date_to = timezone.now().date()
        if date_from is None:
            date_from = date_to.replace(day=1)

        # درآمدها
        revenue_accounts = Account.objects.filter(
            type='revenue', is_postable=True, deleted_at__isnull=True,
        )
        revenue_lines = JournalLine.objects.filter(
            account__in=revenue_accounts,
            journal__date__gte=date_from,
            journal__date__lte=date_to,
            journal__status='posted',
        )
        if cost_center_id:
            revenue_lines = revenue_lines.filter(cost_center_id=cost_center_id)
        total_revenue = revenue_lines.aggregate(t=Sum('credit'))['t'] or Decimal('0')

        # هزینه‌ها
        expense_accounts = Account.objects.filter(
            type='expense', is_postable=True, deleted_at__isnull=True,
        )
        expense_lines = JournalLine.objects.filter(
            account__in=expense_accounts,
            journal__date__gte=date_from,
            journal__date__lte=date_to,
            journal__status='posted',
        )
        if cost_center_id:
            expense_lines = expense_lines.filter(cost_center_id=cost_center_id)
        total_expense = expense_lines.aggregate(t=Sum('debit'))['t'] or Decimal('0')

        return {
            'date_from': date_from.isoformat(),
            'date_to': date_to.isoformat(),
            'total_revenue': str(total_revenue),
            'total_expense': str(total_expense),
            'net_profit': str(total_revenue - total_expense),
            'margin_percentage': (
                float(total_revenue - total_expense) / float(total_revenue) * 100
                if total_revenue > 0 else 0
            ),
        }

    @staticmethod
    def _get_active_period(date):
        """یافتن دوره مالی فعال برای تاریخ"""
        return FiscalPeriod.objects.filter(
            start_date__lte=date,
            end_date__gte=date,
            is_closed=False,
        ).first()

    @staticmethod
    def _generate_journal_number() -> str:
        year = timezone.now().year
        count = JournalHeader.objects.count() + 1
        return f'JRN-{year}-{count:06d}'
