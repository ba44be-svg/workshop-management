"""
Transfers App Configuration
"""
from django.apps import AppConfig


class TransfersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.transfers'
    verbose_name = 'انتقال‌ها'

    def ready(self):
        from . import signals  # noqa
