"""
Development settings
"""
from .base import *  # noqa
import os

DEBUG = True
ALLOWED_HOSTS = ['*']
CORS_ALLOW_ALL_ORIGINS = True

# Emails in development - print to console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Disable rate limiting in development
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['user'] = '1000/min'

# Show internal IP for debugging
INTERNAL_IPS = ['127.0.0.1', '0.0.0.0']

# Django Debug Toolbar (optional)
try:
    import debug_toolbar
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE
except ImportError:
    pass
