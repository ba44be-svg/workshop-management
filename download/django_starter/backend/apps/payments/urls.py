"""
Payments URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'payments'

router = DefaultRouter()
router.register(r'transactions', views.PaymentTransactionViewSet, basename='transaction')
router.register(r'checks', views.CheckPaymentViewSet, basename='check')
router.register(r'cash', views.CashReceiptViewSet, basename='cash')

urlpatterns = [
    path('initiate/', views.PaymentTransactionViewSet.as_view({'post': 'initiate'}),
         name='initiate-payment'),
    path('history/', views.PaymentTransactionViewSet.as_view({'get': 'history'}),
         name='payment-history'),
    path('transactions/<int:pk>/refund/', views.PaymentTransactionViewSet.as_view({'post': 'refund'}),
         name='refund-payment'),
    # Callbacks (بدون احراز هویت)
    path('callback/zarinpal/', views.zarinpal_callback, name='zarinpal-callback'),
    path('callback/idpay/', views.idpay_callback, name='idpay-callback'),
    path('callback/parsian/', views.parsian_callback, name='parsian-callback'),
    # Check actions
    path('checks/<int:pk>/cash/', views.CheckPaymentViewSet.as_view({'post': 'cash'}),
         name='cash-check'),
] + router.urls
