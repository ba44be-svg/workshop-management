"""
Notifications Admin
"""
from django.contrib import admin
from .models import (
    SmsTemplate, SmsQueue, PushNotification, NotificationSchedule,
)


@admin.register(SmsTemplate)
class SmsTemplateAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'active')
    list_filter = ('active',)
    search_fields = ('code', 'name')


@admin.register(SmsQueue)
class SmsQueueAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'status', 'provider', 'scheduled_at',
                    'sent_at', 'retry_count', 'related_user')
    list_filter = ('status', 'provider', 'scheduled_at')
    search_fields = ('recipient', 'message_id')
    date_hierarchy = 'scheduled_at'
    readonly_fields = ('sent_at', 'delivered_at', 'message_id', 'retry_count')


@admin.register(PushNotification)
class PushNotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'status', 'scheduled_at',
                    'sent_at', 'read_at')
    list_filter = ('status', 'scheduled_at')
    search_fields = ('user__username', 'title')
    date_hierarchy = 'scheduled_at'
    readonly_fields = ('sent_at', 'delivered_at', 'read_at', 'fcm_message_id')


@admin.register(NotificationSchedule)
class NotificationScheduleAdmin(admin.ModelAdmin):
    list_display = ('scenario', 'recipient_type', 'channel', 'is_active',
                    'last_run_at', 'next_run_at')
    list_filter = ('scenario', 'channel', 'is_active')
    readonly_fields = ('last_run_at', 'next_run_at')
