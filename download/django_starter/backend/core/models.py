"""
Core base models with Soft Delete and timestamps
"""
from django.db import models


class TimestampedModel(models.Model):
    """مدل پایه با timestamps"""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='+',
        editable=False,
    )

    class Meta:
        abstract = True


class SoftDeleteModel(TimestampedModel):
    """مدل پایه با Soft Delete"""
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        """Soft delete - فقط deleted_at را تنظیم می‌کند"""
        from django.utils import timezone
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at', 'updated_at'])

    def hard_delete(self, *args, **kwargs):
        """حذف فیزیکی"""
        super().delete(*args, **kwargs)


class BaseModel(SoftDeleteModel):
    """مدل پایه با timestamps و soft delete"""
    class Meta:
        abstract = True
