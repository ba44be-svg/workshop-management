"""
Store Portal URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'store_portal'

router = DefaultRouter()
router.register(r'orders', views.StoreOrderViewSet, basename='order')
router.register(r'', views.StorePortalViewSet, basename='portal')

urlpatterns = [
    path('orders/create/', views.StoreOrderViewSet.as_view({'post': 'create_order'}),
         name='create-order'),
    path('orders/<int:pk>/cancel/', views.StoreOrderViewSet.as_view({'post': 'cancel'}),
         name='cancel-order'),
    path('orders/<int:pk>/mark_received/', views.StoreOrderViewSet.as_view({'post': 'mark_received'}),
         name='mark-received'),
    path('orders/<int:pk>/approve/', views.StoreOrderViewSet.as_view({'post': 'approve'}),
         name='approve-order'),
    path('catalog/', views.StorePortalViewSet.as_view({'get': 'catalog'}),
         name='catalog'),
    path('balance/', views.StorePortalViewSet.as_view({'get': 'balance'}),
         name='balance'),
    path('order_history/', views.StorePortalViewSet.as_view({'get': 'order_history'}),
         name='order-history'),
    path('notifications/', views.StorePortalViewSet.as_view({'get': 'notifications'}),
         name='notifications'),
    path('notifications/<int:pk>/mark_read/',
         views.StorePortalViewSet.as_view({'post': 'mark_notification_read'}),
         name='mark-notification-read'),
    path('dashboard/', views.StorePortalViewSet.as_view({'get': 'dashboard'}),
         name='dashboard'),
    path('smart_reorder/', views.StorePortalViewSet.as_view({'get': 'smart_reorder'}),
         name='smart-reorder'),
] + router.urls
