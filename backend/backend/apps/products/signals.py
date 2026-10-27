"""
Products Signals
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Product


@receiver(post_save, sender=Product)
def on_product_created(sender, instance, created, **kwargs):
    """هنگام ساخت محصول جدید"""
    if created:
        # ساخت خودکار بارکد برای محصول
        try:
            from apps.products.services import ProductService
            from apps.products.models import Barcode
            if not instance.barcode:
                barcode_value = ProductService._generate_ean13(instance.id)
                instance.barcode = barcode_value
                instance.save(update_fields=['barcode'])
                Barcode.objects.create(
                    entity_type='product',
                    entity_id=instance.id,
                    barcode_value=barcode_value,
                    qr_code_data=f'PROD:{instance.code}:{instance.id}',
                )
        except Exception:
            pass  # در صورت خطا، بارکد بعداً ساخته می‌شود
