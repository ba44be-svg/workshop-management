"""
Products URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'products'

router = DefaultRouter()
router.register(r'categories', views.ProductCategoryViewSet, basename='category')
router.register(r'', views.ProductViewSet, basename='product')
router.register(r'pricing', views.PricingRuleViewSet, basename='pricing-rule')
router.register(r'barcodes', views.BarcodeViewSet, basename='barcode')

urlpatterns = [
    path('barcodes/scan/', views.BarcodeViewSet.as_view({'post': 'scan'}),
         name='barcode-scan'),
] + router.urls
