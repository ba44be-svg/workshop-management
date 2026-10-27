"""
Workshop App Configuration
"""
from django.apps import AppConfig


class WorkshopConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.workshop'
    verbose_name = 'کارگاه و کارپرداز'

    def ready(self):
        # وارد کردن signals برای اتصال receivers
        from . import signals  # noqa: F401
