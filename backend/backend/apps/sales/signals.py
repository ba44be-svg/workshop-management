"""
Sales Signals — یکپارچگی انبار-حسابداری
نکته: ثبت سند حسابداری خودکار از طریق apps/accounting/signals.py انجام می‌شود
"""
from django.db.models.signals import Signal

# سیگنال سفارشی برای ارسال پس از commit موفق فروش
sale_posted = Signal()
return_posted = Signal()
