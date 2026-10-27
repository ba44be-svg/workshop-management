"""
Sales URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'sales'

router = DefaultRouter()
router.register(r'', views.SalesViewSet, basename='sale')
router.register(r'returns', views.ReturnViewSet, basename='return')

urlpatterns = [
    path('create/', views.SalesViewSet.as_view({'post': 'create_sale'}),
         name='create-sale'),
    path('returns/create/', views.ReturnViewSet.as_view({'post': 'create_return'}),
         name='create-return'),
] + router.urls
