"""
Loyalty URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'loyalty'

router = DefaultRouter()
router.register(r'tiers', views.LoyaltyTierViewSet, basename='tier')
router.register(r'discounts', views.DiscountRuleViewSet, basename='discount')
router.register(r'suggestions', views.ReorderSuggestionViewSet, basename='suggestion')
router.register(r'transactions', views.LoyaltyTransactionViewSet, basename='transaction')

urlpatterns = [
    path('suggestions/generate/',
         views.ReorderSuggestionViewSet.as_view({'post': 'generate'}),
         name='generate-suggestions'),
    path('suggestions/<int:pk>/add_to_cart/',
         views.ReorderSuggestionViewSet.as_view({'post': 'add_to_cart'}),
         name='add-to-cart'),
] + router.urls
