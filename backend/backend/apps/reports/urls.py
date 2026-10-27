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
    # Week-5 new reports
    path('store_receivables/', views.ReportsViewSet.as_view({'get': 'store_receivables'}),
         name='store-receivables'),
    path('store_stock/', views.ReportsViewSet.as_view({'get': 'store_stock'}),
         name='store-stock'),
    path('distributor_stock/', views.ReportsViewSet.as_view({'get': 'distributor_stock'}),
         name='distributor-stock'),
    path('distributor_commission/', views.ReportsViewSet.as_view({'get': 'distributor_commission'}),
         name='distributor-commission'),
    path('waste_report_detailed/', views.ReportsViewSet.as_view({'get': 'waste_report_detailed'}),
         name='waste-report-detailed'),
    path('near_expiry/', views.ReportsViewSet.as_view({'get': 'near_expiry'}),
         name='near-expiry'),
    path('profit_report/', views.ReportsViewSet.as_view({'get': 'profit_report'}),
         name='profit-report'),
]
