"""
Transfers URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'transfers'

router = DefaultRouter()
router.register(r'', views.TransferHeaderViewSet, basename='transfer')
router.register(r'lines', views.TransferLineViewSet, basename='transfer-line')
router.register(r'suggestions', views.TransferSuggestionViewSet, basename='suggestion')

urlpatterns = [
    path('create/', views.TransferHeaderViewSet.as_view({'post': 'create_transfer'}),
         name='create-transfer'),
    path('<int:pk>/approve/', views.TransferHeaderViewSet.as_view({'post': 'approve'}),
         name='approve-transfer'),
    path('<int:pk>/reject/', views.TransferHeaderViewSet.as_view({'post': 'reject'}),
         name='reject-transfer'),
    path('suggestions/generate/',
         views.TransferSuggestionViewSet.as_view({'post': 'generate'}),
         name='generate-suggestions'),
    path('suggestions/<int:pk>/approve/',
         views.TransferSuggestionViewSet.as_view({'post': 'approve'}),
         name='approve-suggestion'),
    path('suggestions/approve_all/',
         views.TransferSuggestionViewSet.as_view({'post': 'approve_all'}),
         name='approve-all-suggestions'),
] + router.urls
