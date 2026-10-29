"""
Sales App Configuration
"""
from django.apps import AppConfig


class SalesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.sales'
    verbose_name = 'فروش و برگشت'

    def ready(self):
        from . import signals  # noqa
