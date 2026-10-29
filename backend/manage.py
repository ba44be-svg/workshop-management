#!/usr/bin/env python
"""
Django's command-line utility for administrative tasks.

نکته: در این پروژه، پکیج `config` (و سایر app‌ها) داخل پوشه‌ی `backend/`
قرار دارند، در حالی که این فایل `manage.py` در ریشه‌ی پروژه است.
برای اینکه Django بتواند `DJANGO_SETTINGS_MODULE` را import کند، باید
پوشه‌ی `backend/` به `sys.path` اضافه شود.
"""
import os
import sys


def main():
    """Run administrative tasks."""
    # اضافه کردن پوشه‌ی backend/ به sys.path تا import config کار کند
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    BACKEND_DIR = os.path.join(BASE_DIR, 'backend')
    if os.path.isdir(BACKEND_DIR) and BACKEND_DIR not in sys.path:
        sys.path.insert(0, BACKEND_DIR)

    # تنظیم پیش‌فرض؛ .env می‌تواند override کند
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local_test')

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
