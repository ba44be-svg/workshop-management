"""
Django settings — Base configuration
تنظیمات پایه که هم در development و هم production استفاده می‌شود
"""
import os
from pathlib import Path
from datetime import timedelta
import environ

# ----- Paths -----
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
APPS_DIR = BASE_DIR / 'backend' / 'apps'

# ----- Environment Variables -----
env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')

# ----- Core Settings -----
SECRET_KEY = env('SECRET_KEY')
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost'])
SITE_URL = env('SITE_URL', default='http://localhost:8000')
ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# ----- Apps -----
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'django_filters',
    'corsheaders',
    'drf_spectacular',
    'django_celery_beat',
    'django_celery_results',
    'storages',
]

LOCAL_APPS = [
    'apps.accounts',
    'apps.products',
    'apps.inventory',
    'apps.production',
    'apps.dispatch',
    'apps.sales',
    'apps.transfers',
    'apps.partners',
    'apps.accounting',
    'apps.workshop',
    'apps.notifications',
    'apps.reports',
    'apps.approval_workflow',
    'apps.store_portal',
    'apps.payments',
    'apps.loyalty',
    'apps.barcode',
    'apps.saman_tax',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ----- Middleware -----
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.RBACMiddleware',
    'core.middleware.ActivityLogMiddleware',
]

# ----- Database -----
DATABASES = {
    'default': env.db('DATABASE_URL'),
}
DATABASES['default']['CONN_MAX_AGE'] = env.int('DB_CONN_MAX_AGE', default=60)

# ----- Cache & Sessions -----
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
        },
        'KEY_PREFIX': 'workshop',
        'TIMEOUT': env.int('CACHE_TTL', default=300),
    }
}
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# ----- Auth -----
AUTH_USER_MODEL = 'accounts.User'
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ----- DRF -----
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.UserRateThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'user': f'{env.int("RATE_LIMIT_PER_MINUTE", default=120)}/min',
    },
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=env.int('JWT_ACCESS_TOKEN_LIFETIME_MINUTES', 15)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=env.int('JWT_REFRESH_TOKEN_LIFETIME_DAYS', 7)),
    'ROTATE_REFRESH_TOKENS': env.bool('JWT_ROTATE_REFRESH_TOKENS', True),
    'AUTH_HEADER_TYPES': ('JWT',),
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'نرم‌افزار جامع مدیریت تولید و پخش',
    'DESCRIPTION': 'سیستم مدیریت تولید، انبار، فروش و حسابداری',
    'VERSION': '2.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'CONTACT': {
        'name': 'تیم ارشد مهندسی نرم‌افزار',
        'email': 'dev@workshop.local',
    },
    'TAGS': [
        {'name': 'auth', 'description': 'احراز هویت'},
        {'name': 'products', 'description': 'مدیریت محصولات'},
        {'name': 'inventory', 'description': 'انبار و موجودی'},
        {'name': 'sales', 'description': 'فروش'},
        {'name': 'accounting', 'description': 'حسابداری'},
        {'name': 'mobile', 'description': 'موبایل عامل'},
        {'name': 'store_portal', 'description': 'پورتال فروشگاه'},
        {'name': 'payments', 'description': 'پرداخت آنلاین'},
    ],
    # ----- احراز هویت JWT در Swagger / OpenAPI schema -----
    'SECURITY': [
        {'jwtAuth': []},
    ],
    'COMPONENTS': {
        'securitySchemes': {
            'jwtAuth': {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT',
                'description': (
                    'توکن JWT دریافتی از POST /api/auth/login/ را اینجا وارد کنید. '
                    'نکته: سرور پیشوند "JWT" را در هدر Authorization انتظار دارد، '
                    'نه "Bearer".'
                ),
            }
        }
    },
}

# ----- Celery -----
CELERY_BROKER_URL = env('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='django-db')
CELERY_TIMEZONE = env('CELERY_TIMEZONE', default='Asia/Tehran')
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# ----- Static & Media -----
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ----- Internationalization -----
LANGUAGE_CODE = 'fa-ir'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_TZ = True
LANGUAGES = [
    ('fa-ir', 'Persian'),
    ('en-us', 'English'),
]
LOCALE_PATHS = [BASE_DIR / 'locale']

# ----- Static files -----
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ----- Default primary key field -----
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ----- Templates -----
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ----- Logging -----
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'verbose'},
    },
    'root': {'handlers': ['console'], 'level': 'INFO'},
    'loggers': {
        'django': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'apps': {'handlers': ['console'], 'level': 'DEBUG', 'propagate': False},
        'celery': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
    },
}

# ----- Sentry -----
if env('SENTRY_DSN', default=''):
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    sentry_sdk.init(
        dsn=env('SENTRY_DSN'),
        environment=env('SENTRY_ENVIRONMENT', default='development'),
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
    )

# ----- Persian Calendar Helper -----
USE_PERSIAN_CALENDAR = True
