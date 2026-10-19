"""
Reports URLs
"""
from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('dashboard/', views.ReportsViewSet.as_view({'get': 'dashboard'}),
         name='dashboard'),
    path('geo_heatmap/', views.ReportsViewSet.as_view({'get': 'geo_heatmap'}),
         name='geo-heatmap'),
    path('waste_report/', views.ReportsViewSet.as_view({'get': 'waste_report'}),
         name='waste-report'),
    path('top_products/', views.ReportsViewSet.as_view({'get': 'top_products'}),
         name='top-products'),
    path('top_stores/', views.ReportsViewSet.as_view({'get': 'top_stores'}),
         name='top-stores'),
    path('top_distributors/', views.ReportsViewSet.as_view({'get': 'top_distributors'}),
         name='top-distributors'),
    path('sales_trend/', views.ReportsViewSet.as_view({'get': 'sales_trend'}),
         name='sales-trend'),
]
