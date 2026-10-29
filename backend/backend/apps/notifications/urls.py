"""
Notifications URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'notifications'

router = DefaultRouter()
router.register(r'templates', views.SmsTemplateViewSet, basename='template')
router.register(r'sms', views.SmsQueueViewSet, basename='sms')
router.register(r'push', views.PushNotificationViewSet, basename='push')
router.register(r'schedules', views.NotificationScheduleViewSet, basename='schedule')

urlpatterns = [
    path('sms/send/', views.SmsQueueViewSet.as_view({'post': 'send'}),
         name='send-sms'),
    path('sms/retry_failed/', views.SmsQueueViewSet.as_view({'post': 'retry_failed'}),
         name='retry-failed-sms'),
    path('push/send/', views.PushNotificationViewSet.as_view({'post': 'send'}),
         name='send-push'),
    path('push/unread_count/', views.PushNotificationViewSet.as_view({'get': 'unread_count'}),
         name='push-unread-count'),
    path('push/<int:pk>/mark_read/', views.PushNotificationViewSet.as_view({'post': 'mark_read'}),
         name='push-mark-read'),
] + router.urls
