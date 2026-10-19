"""
Inventory URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'inventory'

router = DefaultRouter()
router.register(r'warehouses', views.WarehouseViewSet, basename='warehouse')
router.register(r'lots', views.InventoryLotViewSet, basename='lot')
router.register(r'movements', views.InventoryMovementViewSet, basename='movement')
router.register(r'balances', views.StockBalanceViewSet, basename='balance')

urlpatterns = [
    # FEFO endpoint (مهم‌ترین endpoint)
    path('allocate-fefo/', views.FEFOViewSet.as_view({'post': 'allocate'}),
         name='allocate-fefo'),
] + router.urls
