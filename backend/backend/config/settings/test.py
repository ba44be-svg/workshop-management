"""
Test settings — تنظیمات تست
"""
from .base import *  # noqa

DEBUG = True

# در تست‌ها از SQLite استفاده می‌کنیم برای سرعت بیشتر
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# بدون Redis و Celery
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
CELERY_TASK_ALWAYS_EAGER = True
CELERY_BROKER_URL = 'memory://'

# Rate limit بالا برای تست‌ها
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['user'] = '1000/min'

# بدون Sentry
SENTRY_DSN = ''

# Password hasher سریع برای تست‌ها
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]
