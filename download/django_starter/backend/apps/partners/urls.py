"""
Partners URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'partners'

router = DefaultRouter()
router.register(r'distributors', views.DistributorViewSet, basename='distributor')
router.register(r'stores', views.StoreViewSet, basename='store')
router.register(r'customers', views.CustomerViewSet, basename='customer')
router.register(r'loyalty', views.LoyaltyPointViewSet, basename='loyalty')

urlpatterns = [
    path('stores/by_tier/', views.StoreViewSet.as_view({'get': 'by_tier'}),
         name='stores-by-tier'),
    path('stores/geo_points/', views.StoreViewSet.as_view({'get': 'geo_points'}),
         name='stores-geo-points'),
] + router.urls
