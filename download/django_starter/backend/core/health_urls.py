"""
Health check endpoints
"""
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache


def health_check(request):
    """بررسی سلامت سیستم و وابستگی‌ها"""
    checks = {
        'database': 'unknown',
        'redis': 'unknown',
        'celery': 'unknown',
    }
    overall = 'ok'

    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
        checks['database'] = 'ok'
    except Exception as e:
        checks['database'] = f'error: {str(e)[:100]}'
        overall = 'error'

    # Redis check
    try:
        cache.set('health_check', '1', 5)
        cache.get('health_check')
        checks['redis'] = 'ok'
    except Exception as e:
        checks['redis'] = f'error: {str(e)[:100]}'
        overall = 'degraded'

    # Celery check (simplified)
    try:
        from django_celery_results.models import TaskResult
        recent = TaskResult.objects.filter(status='SUCCESS').count()
        checks['celery'] = f'ok ({recent} recent successful tasks)'
    except Exception:
        checks['celery'] = 'unknown'

    status_code = 200 if overall == 'ok' else 503
    return JsonResponse({
        'status': overall,
        'checks': checks,
        'version': '2.0.0',
    }, status=status_code)


def readiness_check(request):
    """آماده بودن برای ترافیک"""
    return JsonResponse({'status': 'ready'})


def liveness_check(request):
    """زنده بودن"""
    return JsonResponse({'status': 'alive'})


urlpatterns = [
    ('', health_check),
    ('/ready/', readiness_check),
    ('/live/', liveness_check),
]
