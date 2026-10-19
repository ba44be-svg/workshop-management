"""
Accounts Models — User, Role, Permission, UserProfile
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Custom User model with role-based access"""

    class RoleChoices(models.TextChoices):
        MANAGER = 'manager', _('مدیر')
        ACCOUNTANT = 'accountant', _('حسابدار')
        STOREKEEPER = 'storekeeper', _('انباردار')
        DISTRIBUTOR = 'distributor', _('عامل پخش')
        STORE_OWNER = 'store_owner', _('فروشگاه')

    role = models.CharField(
        max_length=20,
        choices=RoleChoices.choices,
        default=RoleChoices.STOREKEEPER,
        verbose_name=_('نقش'),
    )
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True,
                             verbose_name=_('شماره موبایل'))
    fcm_token = models.TextField(null=True, blank=True,
                                   verbose_name=_('Firebase Push Token'))

    class Meta:
        db_table = 'users'
        verbose_name = _('کاربر')
        verbose_name_plural = _('کاربران')

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'

    @property
    def is_manager(self):
        return self.role == self.RoleChoices.MANAGER

    @property
    def is_store_owner(self):
        return self.role == self.RoleChoices.STORE_OWNER


class Role(models.Model):
    """نقش‌های سیستم"""
    name = models.CharField(max_length=100, unique=True, verbose_name=_('نام'))
    code = models.CharField(max_length=50, unique=True, verbose_name=_('کد'))
    description = models.TextField(blank=True, verbose_name=_('توضیحات'))
    is_active = models.BooleanField(default=True, verbose_name=_('فعال'))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'roles'
        verbose_name = _('نقش')
        verbose_name_plural = _('نقش‌ها')

    def __str__(self):
        return self.name


class Permission(models.Model):
    """دسترسی‌های per-action"""
    code = models.CharField(max_length=100, unique=True, verbose_name=_('کد'))
    name = models.CharField(max_length=200, verbose_name=_('نام'))
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'permissions'
        verbose_name = _('دسترسی')
        verbose_name_plural = _('دسترسی‌ها')

    def __str__(self):
        return f'{self.code} - {self.name}'


class UserProfile(models.Model):
    """پروفایل اضافه کاربر"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    distributor = models.ForeignKey('partners.Distributor', on_delete=models.SET_NULL,
                                     null=True, blank=True)
    store = models.ForeignKey('partners.Store', on_delete=models.SET_NULL,
                              null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    phone_verified = models.BooleanField(default=False)
    two_factor_enabled = models.BooleanField(default=False)
    notification_prefs = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'user_profiles'

    def __str__(self):
        return f'Profile for {self.user.username}'


class ActivityLog(models.Model):
    """لاگ فعالیت‌های مهم برای Audit Trail"""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50)  # create, update, delete, approve
    entity_type = models.CharField(max_length=50)
    entity_id = models.BigIntegerField(null=True, blank=True)
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'activity_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['entity_type', 'entity_id']),
        ]

    def __str__(self):
        return f'{self.user} - {self.action} - {self.entity_type}'
