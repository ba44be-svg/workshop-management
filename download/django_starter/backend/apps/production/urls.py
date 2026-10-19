"""
Production URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'production'

router = DefaultRouter()
router.register(r'_batches', views.ProductionBatchViewSet, basename='batch')
router.register(r'consumptions', views.ProductionConsumptionViewSet, basename='consumption')
router.register(r'outputs', views.ProductionOutputViewSet, basename='output')

urlpatterns = [
    path('batches/', include(router.urls[0:1])),  # فقط batch
    path('batches/create/', views.ProductionBatchViewSet.as_view({'post': 'create_batch'}),
         name='create-batch'),
    path('batches/<int:pk>/start/', views.ProductionBatchViewSet.as_view({'post': 'start'}),
         name='start-batch'),
    path('batches/<int:pk>/cancel/', views.ProductionBatchViewSet.as_view({'post': 'cancel'}),
         name='cancel-batch'),
    path('batches/consume_material/',
         views.ProductionBatchViewSet.as_view({'post': 'consume_material'}),
         name='consume-material'),
    path('batches/complete/',
         views.ProductionBatchViewSet.as_view({'post': 'complete'}),
         name='complete-batch'),
    path('batches/report/',
         views.ProductionBatchViewSet.as_view({'get': 'report'}),
         name='batch-report'),
    path('consumptions/', include(router.urls[1:2])),
    path('outputs/', include(router.urls[2:3])),
]
