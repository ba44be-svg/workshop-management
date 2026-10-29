"""
Notifications Serializers
"""
from rest_framework import serializers
from .models import (
    SmsTemplate, SmsQueue, PushNotification, NotificationSchedule,
)


class SmsTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SmsTemplate
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class SmsQueueSerializer(serializers.ModelSerializer):
    template_code = serializers.CharField(source='template.code', read_only=True, default='')
    message_text = serializers.SerializerMethodField()

    class Meta:
        model = SmsQueue
        fields = ('id', 'recipient', 'template', 'template_code', 'context_data',
                  'raw_text', 'message_text', 'status', 'scheduled_at', 'sent_at',
                  'delivered_at', 'message_id', 'provider', 'retry_count',
                  'next_retry_at', 'error_message', 'related_doc_type', 'related_doc_id')
        read_only_fields = ('id', 'scheduled_at', 'sent_at', 'delivered_at',
                          'message_id', 'retry_count', 'next_retry_at', 'error_message',
                          'status')

    def get_message_text(self, obj):
        return obj.message_text


class PushNotificationSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = PushNotification
        fields = ('id', 'user', 'user_username', 'title', 'body', 'data',
                  'status', 'scheduled_at', 'sent_at', 'read_at',
                  'fcm_message_id', 'related_doc_type', 'related_doc_id')
        read_only_fields = ('id', 'scheduled_at', 'sent_at', 'delivered_at',
                          'read_at', 'fcm_message_id', 'status')


class NotificationScheduleSerializer(serializers.ModelSerializer):
    scenario_display = serializers.CharField(source='get_scenario_display', read_only=True)
    channel_display = serializers.CharField(source='get_channel_display', read_only=True)

    class Meta:
        model = NotificationSchedule
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'last_run_at', 'next_run_at')


class SendSmsInputSerializer(serializers.Serializer):
    recipient = serializers.CharField(max_length=20)
    template_code = serializers.CharField(required=False, allow_null=True)
    context = serializers.JSONField(required=False)
    raw_text = serializers.CharField(required=False, allow_blank=True)
    immediate = serializers.BooleanField(default=False)


class SendPushInputSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    title = serializers.CharField(max_length=200)
    body = serializers.CharField()
    data = serializers.JSONField(required=False)
