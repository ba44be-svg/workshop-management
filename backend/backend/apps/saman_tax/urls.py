"""
Saman Tax URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'saman_tax'

router = DefaultRouter()
router.register(r'invoices', views.TaxInvoiceViewSet, basename='invoice')

urlpatterns = [
    path('invoices/send/', views.TaxInvoiceViewSet.as_view({'post': 'send'}),
         name='send-invoice'),
    path('invoices/check_status/', views.TaxInvoiceViewSet.as_view({'post': 'check_status'}),
         name='check-status'),
    path('invoices/cancel/', views.TaxInvoiceViewSet.as_view({'post': 'cancel'}),
         name='cancel-invoice'),
    path('invoices/retry_failed/', views.TaxInvoiceViewSet.as_view({'post': 'retry_failed'}),
         name='retry-failed'),
] + router.urls
