"""
Accounts App Configuration
"""
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'
    verbose_name = 'کاربران و نقش‌ها'

    def ready(self):
        """Import signals when app is ready"""
        from . import signals  # noqa
