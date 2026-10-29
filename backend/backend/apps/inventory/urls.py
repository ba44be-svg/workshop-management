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
router.register(r'wastes', views.WasteDocumentViewSet, basename='waste')

urlpatterns = [
    # FEFO endpoint (مهم‌ترین endpoint)
    path('allocate-fefo/', views.FEFOViewSet.as_view({'post': 'allocate'}),
         name='allocate-fefo'),
    # ساخت سند ضایعات (custom action)
    path('wastes/create_waste/', views.WasteDocumentViewSet.as_view({'post': 'create_waste'}),
         name='create-waste'),
] + router.urls
