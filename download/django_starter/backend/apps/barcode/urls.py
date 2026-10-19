"""
Barcode URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'barcode'

router = DefaultRouter()
router.register(r'', views.BarcodeViewSet, basename='barcode')
router.register(r'scans', views.BarcodeScanViewSet, basename='scan')

urlpatterns = [
    path('generate/', views.BarcodeViewSet.as_view({'post': 'generate'}),
         name='generate-barcode'),
    path('scan/', views.BarcodeViewSet.as_view({'post': 'scan'}),
         name='scan-barcode'),
    path('<str:barcode_value>/image/', views.BarcodeViewSet.as_view({'get': 'image'}),
         name='barcode-image'),
    path('<str:barcode_value>/qr_image/', views.BarcodeViewSet.as_view({'get': 'qr_image'}),
         name='qr-image'),
] + router.urls
