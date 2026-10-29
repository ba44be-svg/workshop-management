"""
Production settings — Cloud-ready (Render/Vercel)
پشتیبانی از PostgreSQL ابری + SQLite محلی
"""
from .base import *  # noqa
import os

# ----- Core -----
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

# ----- Database -----
# در محیط ابری: PostgreSQL از DATABASE_URL
# در محیط محلی: SQLite (اگه DATABASE_URL نباشه)
import dj_database_url
DATABASES = {
    'default': dj_database_url.parse(
        os.environ.get('DATABASE_URL', 'sqlite:///dev_test.db')
    )
}
DATABASES['default']['CONN_MAX_AGE'] = 60

# ----- Cache (بدون Redis — از LocMem استفاده می‌کنیم) -----
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# ----- Celery (حالت eager — بدون broker) -----
CELERY_TASK_ALWAYS_EAGER = True
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'memory://')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'django-db')

# ----- CORS -----
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# ----- Static files -----
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Whitenoise برای سرو فایل‌های استاتیک
MIDDLEWARE = MIDDLEWARE + ['whitenoise.middleware.WhiteNoiseMiddleware']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ----- Security -----
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# ----- Rate Limit -----
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['user'] = '1000/min'

# ----- Sentry (اختیاری) -----
SENTRY_DSN = os.environ.get('SENTRY_DSN', '')

# ----- Session -----
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
