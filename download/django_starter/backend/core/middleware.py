"""
Custom Middleware
"""
import json
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)


class RBACMiddleware:
    """اعمال کنترل دسترسی مبتنی بر نقش"""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response


class ActivityLogMiddleware:
    """ثبت خودکار فعالیت‌های مهم"""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Log only mutation methods (POST, PUT, PATCH, DELETE)
        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE') and response.status_code < 400:
            self._log_activity(request, response)
        return response

    def _log_activity(self, request, response):
        """ثبت در ActivityLog"""
        try:
            from apps.accounts.models import ActivityLog
            if request.user.is_authenticated:
                ActivityLog.objects.create(
                    user=request.user,
                    action=request.method.lower(),
                    entity_type=request.path,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                )
        except Exception as e:
            logger.error(f'Failed to log activity: {e}')
