"""
Accounts Views
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import User, Role, Permission, UserProfile
from .serializers import (
    UserSerializer, RoleSerializer, PermissionSerializer,
    UserProfileSerializer,
)
from core.permissions import IsManager


class UserViewSet(viewsets.ModelViewSet):
    """API برای مدیریت کاربران"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsManager]
    filterset_fields = ['role', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone']
    ordering_fields = ['date_joined', 'username']

    @action(detail=False, methods=['get'])
    def me(self, request):
        """اطلاعات کاربر فعلی"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        user = self.get_object()
        user.is_active = True
        user.save()
        return Response({'status': 'activated'})

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response({'status': 'deactivated'})


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, IsManager]


class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated]


class MeView(APIView):
    """اطلاعات کاربر فعلی"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class LogoutView(APIView):
    """Logout - invalidate refresh token"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # In a real implementation, add refresh token to blacklist
        return Response({'detail': 'خروج با موفقیت انجام شد'}, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    """تغییر رمز عبور"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not user.check_password(old_password):
            return Response({'detail': 'رمز عبور فعلی اشتباه است'},
                          status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({'detail': 'رمز عبور با موفقیت تغییر کرد'})


class RegisterFCMTokenView(APIView):
    """ثبت Firebase Cloud Messaging Token"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token = request.data.get('fcm_token')
        if not token:
            return Response({'detail': 'fcm_token لازم است'},
                          status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        user.fcm_token = token
        user.save()
        return Response({'detail': 'Token با موفقیت ثبت شد'})
