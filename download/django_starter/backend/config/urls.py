"""
Django URL configuration — Root URLs
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

# Admin site title
admin.site.site_header = 'نرم‌افزار جامع مدیریت تولید و پخش'
admin.site.site_title = 'مدیریت تولید و پخش'
admin.site.index_title = 'پنل مدیریت'

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API Documentation (OpenAPI/Swagger)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Authentication
    path('api/auth/', include('apps.accounts.urls')),
    path('api/auth/', include('rest_framework.urls')),

    # Core Apps
    path('api/products/', include('apps.products.urls')),
    path('api/inventory/', include('apps.inventory.urls')),
    path('api/production/', include('apps.production.urls')),
    path('api/dispatch/', include('apps.dispatch.urls')),
    path('api/sales/', include('apps.sales.urls')),
    path('api/transfers/', include('apps.transfers.urls')),
    path('api/partners/', include('apps.partners.urls')),
    path('api/accounting/', include('apps.accounting.urls')),
    path('api/reports/', include('apps.reports.urls')),

    # New Apps (v2.0)
    path('api/approval/', include('apps.approval_workflow.urls')),
    path('api/store-portal/', include('apps.store_portal.urls')),
    path('api/payments/', include('apps.payments.urls')),
    path('api/loyalty/', include('apps.loyalty.urls')),
    path('api/barcode/', include('apps.barcode.urls')),
    path('api/tax/', include('apps.saman_tax.urls')),

    # Notifications
    path('api/notifications/', include('apps.notifications.urls')),

    # Health check
    path('api/health/', include('core.health_urls')),
]

# Static and Media
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
