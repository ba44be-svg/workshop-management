"""
Accounting URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'accounting'

router = DefaultRouter()
router.register(r'accounts', views.AccountViewSet, basename='account')
router.register(r'cost-centers', views.CostCenterViewSet, basename='cost-center')
router.register(r'periods', views.FiscalPeriodViewSet, basename='period')
router.register(r'templates', views.JournalTemplateViewSet, basename='template')
router.register(r'journals', views.JournalHeaderViewSet, basename='journal')
router.register(r'journal-lines', views.JournalLineViewSet, basename='journal-line')
router.register(r'exchange-rates', views.ExchangeRateViewSet, basename='exchange-rate')

urlpatterns = [
    path('accounts/tree/', views.AccountViewSet.as_view({'get': 'tree'}),
         name='account-tree'),
    path('periods/<int:pk>/close/', views.FiscalPeriodViewSet.as_view({'post': 'close'}),
         name='period-close'),
    path('journals/create_manual/', views.JournalHeaderViewSet.as_view({'post': 'create_manual'}),
         name='create-manual-journal'),
    path('journals/<int:pk>/reverse/', views.JournalHeaderViewSet.as_view({'post': 'reverse'}),
         name='reverse-journal'),
    path('journals/trial_balance/', views.JournalHeaderViewSet.as_view({'get': 'trial_balance'}),
         name='trial-balance'),
    path('journals/profit_loss/', views.JournalHeaderViewSet.as_view({'get': 'profit_loss'}),
         name='profit-loss'),
] + router.urls
