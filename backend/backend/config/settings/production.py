"""تنظیمات تولید (Production)"""
from .base import *  # noqa
import os

DEBUG = False
ALLOWED_HOSTS = ['*']

# دیتابیس PostgreSQL (از DATABASE_URL)
import dj_database_url
DATABASES = {
    'default': dj_database_url.parse(os.environ.get('DATABASE_URL', 'sqlite:///db.sqlite3'))
}

# CORS
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# WhiteNoise برای فایل‌های استاتیک
MIDDLEWARE = MIDDLEWARE + ['whitenoise.middleware.WhiteNoiseMiddleware']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Celery
CELERY_TASK_ALWAYS_EAGER = True
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'memory://')

# امنیت
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# ثابت
STATIC_URL = '/static/'
MEDIA_URL = '/media/'
