"""
Approval Workflow Service — منطق تأیید اسناد
"""
from typing import Optional
from django.db import transaction
from django.utils import timezone
from .models import (
    ApprovalQueue, ApprovalRule,
    ApprovalStatus, ApprovalPriority, RefDocType,
)


class ApprovalService:
    """سرویس جریان تأیید"""

    @staticmethod
    @transaction.atomic
    def create_request(
        *,
        ref_doc_type: str,
        ref_doc_id: int,
        requested_by_id: int,
        priority: str = ApprovalPriority.MEDIUM,
        assigned_to_id: Optional[int] = None,
        notes: str = '',
    ) -> ApprovalQueue:
        """ثبت یک سند در صف تأیید"""

        # اگر قبلاً ثبت شده، خطا نده
        existing = ApprovalQueue.objects.filter(
            ref_doc_type=ref_doc_type, ref_doc_id=ref_doc_id,
        ).first()
        if existing and existing.status in [ApprovalStatus.PENDING, ApprovalStatus.REVIEWING]:
            return existing

        # اگر قانون تأیید وجود دارد، تنظیمات خودکار را اعمال کن
        if not assigned_to_id or not priority:
            try:
                rule = ApprovalRule.objects.get(doc_type=ref_doc_type, is_active=True)
                if not assigned_to_id and rule.auto_assign_to:
                    assigned_to_id = rule.auto_assign_to_id
                if priority == ApprovalPriority.MEDIUM and rule.auto_priority:
                    priority = rule.auto_priority
            except ApprovalRule.DoesNotExist:
                pass

        # اگر آیتم قدیمی رد/تأیید شده بود، یک رکورد جدید بساز
        if existing:
            existing.delete()

        return ApprovalQueue.objects.create(
            ref_doc_type=ref_doc_type,
            ref_doc_id=ref_doc_id,
            requested_by_id=requested_by_id,
            assigned_to_id=assigned_to_id,
            status=ApprovalStatus.PENDING,
            priority=priority,
            notes=notes,
        )

    @staticmethod
    @transaction.atomic
    def mark_reviewing(*, approval_id: int, manager_id: int) -> ApprovalQueue:
        """شروع بررسی توسط مدیر"""
        approval = ApprovalQueue.objects.select_for_update().get(id=approval_id)
        if approval.status != ApprovalStatus.PENDING:
            raise ValueError(
                f'این آیتم در وضعیت {approval.status} است و قابل بررسی نیست'
            )
        approval.status = ApprovalStatus.REVIEWING
        approval.assigned_to_id = manager_id
        approval.save(update_fields=['status', 'assigned_to', 'updated_at'])
        return approval

    @staticmethod
    @transaction.atomic
    def approve(
        *,
        approval_id: int,
        approved_by_id: int,
        reason: str = '',
        notes: str = '',
    ) -> dict:
        """
        تأیید یک آیتم و اجرای عملیات مرتبط.

        اگر آیتم از نوع sales_draft باشد، آن را به SalesHeader تبدیل می‌کند.
        اگر از نوع store_order باشد، DispatchHeader می‌سازد.
        اگر از نوع transfer باشد، انتقال را تأیید می‌کند.
        """
        approval = ApprovalQueue.objects.select_for_update().get(id=approval_id)
        if approval.status not in [ApprovalStatus.PENDING, ApprovalStatus.REVIEWING]:
            raise ValueError(
                f'این آیتم در وضعیت {approval.status} است و قابل تأیید نیست'
            )

        approval.status = ApprovalStatus.APPROVED
        approval.decision_reason = reason
        approval.decided_at = timezone.now()
        approval.decided_by_id = approved_by_id
        if notes:
            approval.notes = f'{approval.notes}\n\n{notes}'.strip()
        approval.save(update_fields=['status', 'decision_reason', 'decided_at',
                                     'decided_by', 'notes', 'updated_at'])

        # اجرای عملیات مرتبط با نوع سند
        posted_doc = ApprovalService._process_approved_doc(approval)

        # به‌روزرسانی وضعیت به posted
        approval.status = ApprovalStatus.POSTED
        approval.save(update_fields=['status', 'updated_at'])

        return {
            'approval': approval,
            'posted_doc': posted_doc,
        }

    @staticmethod
    @transaction.atomic
    def reject(
        *,
        approval_id: int,
        rejected_by_id: int,
        reason: str,
    ) -> ApprovalQueue:
        """رد یک آیتم"""
        approval = ApprovalQueue.objects.select_for_update().get(id=approval_id)
        if approval.status not in [ApprovalStatus.PENDING, ApprovalStatus.REVIEWING]:
            raise ValueError(
                f'این آیتم در وضعیت {approval.status} است و قابل رد نیست'
            )

        approval.status = ApprovalStatus.REJECTED
        approval.decision_reason = reason
        approval.decided_at = timezone.now()
        approval.decided_by_id = rejected_by_id
        approval.save(update_fields=['status', 'decision_reason', 'decided_at',
                                     'decided_by', 'updated_at'])

        # اگر سند مرجع وضعیت قابل‌تغییری دارد، آن را هم رد کن
        ApprovalService._update_rejected_doc(approval)

        # ارسال اعلان به درخواست‌کننده
        if approval.requested_by:
            from apps.notifications.services import PushService
            try:
                PushService.send_to_user(
                    user_id=approval.requested_by_id,
                    title='رد پیش‌نویس',
                    body=f'پیش‌نویس {approval.ref_doc_type}:{approval.ref_doc_id} رد شد. '
                         f'دلیل: {reason}',
                    data={
                        'doc_type': approval.ref_doc_type,
                        'doc_id': approval.ref_doc_id,
                    },
                )
            except Exception:
                pass

        return approval

    @staticmethod
    def _process_approved_doc(approval: ApprovalQueue):
        """اجرای عملیات مرتبط با سند تأییدشده"""
        if approval.ref_doc_type == RefDocType.SALES_DRAFT:
            # تبدیل پیش‌نویس به سند فروش واقعی
            return ApprovalService._convert_sales_draft_to_sale(approval)

        elif approval.ref_doc_type == RefDocType.STORE_ORDER:
            # تبدیل سفارش به سند پخش
            return ApprovalService._convert_store_order_to_dispatch(approval)

        elif approval.ref_doc_type == RefDocType.TRANSFER:
            # تأیید انتقال
            from apps.transfers.services import TransferService
            return TransferService.approve_transfer(
                transfer_id=approval.ref_doc_id,
                approved_by_id=approval.decided_by_id,
            )

        return None

    @staticmethod
    def _convert_sales_draft_to_sale(approval):
        """تبدیل پیش‌نویس فروش به سند فروش واقعی"""
        # این متد در فاز ۶ تکمیل می‌شود (وقتی SalesDraft app آماده شد)
        # فعلاً Placeholder
        from apps.sales.services import SalesService
        # TODO: از apps.store_portal.models.SalesDraft بخوان
        return None

    @staticmethod
    def _convert_store_order_to_dispatch(approval):
        """تبدیل سفارش فروشگاه به سند پخش"""
        # این متد در فاز ۶ تکمیل می‌شود (وقتی store_portal app آماده شد)
        return None

    @staticmethod
    def _update_rejected_doc(approval: ApprovalQueue):
        """به‌روزرسانی سند مرجع هنگام رد"""
        if approval.ref_doc_type == RefDocType.SALES_DRAFT:
            # به‌روزرسانی وضعیت پیش‌نویس به rejected
            pass  # در فاز ۶
        elif approval.ref_doc_type == RefDocType.STORE_ORDER:
            # به‌روزرسانی وضعیت سفارش به rejected
            pass  # در فاز ۶

    @staticmethod
    def get_pending_count(user_id: int = None) -> int:
        """تعداد آیتم‌های در انتظار تأیید"""
        qs = ApprovalQueue.objects.filter(status=ApprovalStatus.PENDING)
        if user_id:
            qs = qs.filter(assigned_to_id=user_id)
        return qs.count()

    @staticmethod
    def get_pending_list(user_id: int = None, doc_type: str = None):
        """لیست آیتم‌های در انتظار"""
        qs = ApprovalQueue.objects.filter(
            status__in=[ApprovalStatus.PENDING, ApprovalStatus.REVIEWING]
        ).select_related('requested_by', 'assigned_to')

        if user_id:
            qs = qs.filter(
                models.Q(assigned_to_id=user_id) | models.Q(assigned_to__isnull=True)
            )
        if doc_type:
            qs = qs.filter(ref_doc_type=doc_type)

        return qs.order_by('-priority', '-requested_at')


from django.db import models  # noqa
