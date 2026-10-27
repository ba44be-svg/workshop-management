"""
Local testing settings — بدون نیاز به PostgreSQL/Redis
"""
from .base import *  # noqa

DEBUG = True
ALLOWED_HOSTS = ['*']

# CORS — اجازه دسترسی React/Next.js dev server به API
# (بدون این تنظیم، preflight از localhost:3000 رد می‌شود و fetch خطای TypeError می‌دهد)
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Override DATABASES to use SQLite directly
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'dev_test.db',
    }
}

# بدون Redis — از local memory cache استفاده کن
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Celery در حالت eager (بدون broker)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_BROKER_URL = 'memory://'

# Rate limit بالا برای تست
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['user'] = '1000/min'

# بدون Sentry
SENTRY_DSN = ''

# Password hasher سریع
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# بدون Redis sessions
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
