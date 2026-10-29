"""
Notifications Views
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core.permissions import IsManager
from .models import (
    SmsTemplate, SmsQueue, PushNotification, NotificationSchedule,
)
from .serializers import (
    SmsTemplateSerializer, SmsQueueSerializer, PushNotificationSerializer,
    NotificationScheduleSerializer, SendSmsInputSerializer, SendPushInputSerializer,
)
from .services import NotificationService, PushService


class SmsTemplateViewSet(viewsets.ModelViewSet):
    queryset = SmsTemplate.objects.all()
    serializer_class = SmsTemplateSerializer
    permission_classes = [IsAuthenticated, IsManager]
    search_fields = ['code', 'name']
    ordering = ['code']


class SmsQueueViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SmsQueue.objects.all()
    serializer_class = SmsQueueSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'provider', 'related_user']
    ordering = ['-scheduled_at']

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsManager])
    def send(self, request):
        """ارسال پیامک جدید"""
        serializer = SendSmsInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        queue_item = NotificationService.send_sms(
            recipient=data['recipient'],
            template_code=data.get('template_code'),
            context=data.get('context'),
            raw_text=data.get('raw_text', ''),
            immediate=data.get('immediate', False),
            related_user=request.user,
        )
        return Response(
            SmsQueueSerializer(queue_item, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=['post'])
    def retry_failed(self, request):
        """تلاش مجدد برای پیامک‌های ناموفق"""
        from core.tasks import retry_failed_sms
        retry_failed_sms.delay()
        return Response({'detail': 'Retry queued for failed SMS'})


class PushNotificationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PushNotification.objects.all()
    serializer_class = PushNotificationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['user', 'status']
    ordering = ['-scheduled_at']

    def get_queryset(self):
        """کاربر فقط Pushهای خودش را می‌بیند (به‌جز مدیر)"""
        qs = super().get_queryset()
        if self.request.user.role != 'manager':
            qs = qs.filter(user=self.request.user)
        return qs

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsManager])
    def send(self, request):
        """ارسال Push به کاربر"""
        serializer = SendPushInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        push = PushService.send_to_user(
            user_id=data['user_id'],
            title=data['title'],
            body=data['body'],
            data=data.get('data', {}),
        )
        return Response(
            PushNotificationSerializer(push, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """تعداد اعلان‌های خوانده‌نشده کاربر فعلی"""
        count = PushService.get_unread_count(request.user.id)
        return Response({'count': count})

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """علامت‌گذاری به‌عنوان خوانده‌شده"""
        success = PushService.mark_as_read(push_id=int(pk))
        return Response({'success': success})


class NotificationScheduleViewSet(viewsets.ModelViewSet):
    queryset = NotificationSchedule.objects.all()
    serializer_class = NotificationScheduleSerializer
    permission_classes = [IsAuthenticated, IsManager]
    filterset_fields = ['scenario', 'channel', 'is_active']
    ordering = ['next_run_at']
