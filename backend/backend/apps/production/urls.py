"""
Production URLs — صریح با path() برای رفع 404 در batches/

All endpoints under /api/production/:
  - batches/                      GET list  / POST create
  - batches/<int:pk>/             GET/PUT/PATCH/DELETE detail
  - batches/create/               POST create_batch action
  - batches/<int:pk>/start/       POST start
  - batches/<int:pk>/cancel/      POST cancel
  - batches/consume_material/     POST consume_material
  - batches/complete/             POST complete
  - batches/report/               GET report
  - consumptions/                 GET list (ReadOnly)
  - consumptions/<int:pk>/        GET detail
  - outputs/                      GET list
  - outputs/<int:pk>/             GET detail
"""
from django.urls import path
from . import views

app_name = 'production'

urlpatterns = [
    # ----- Batches (ModelViewSet) -----
    path('batches/', views.ProductionBatchViewSet.as_view({
        'get': 'list',
        'post': 'create',
    }), name='batch-list'),
    path('batches/create/', views.ProductionBatchViewSet.as_view({'post': 'create_batch'}),
         name='create-batch'),
    path('batches/consume_material/',
         views.ProductionBatchViewSet.as_view({'post': 'consume_material'}),
         name='consume-material'),
    path('batches/complete/',
         views.ProductionBatchViewSet.as_view({'post': 'complete'}),
         name='complete-batch'),
    path('batches/report/',
         views.ProductionBatchViewSet.as_view({'get': 'report'}),
         name='batch-report'),
    path('batches/<int:pk>/start/',
         views.ProductionBatchViewSet.as_view({'post': 'start'}),
         name='start-batch'),
    path('batches/<int:pk>/cancel/',
         views.ProductionBatchViewSet.as_view({'post': 'cancel'}),
         name='cancel-batch'),
    path('batches/<int:pk>/', views.ProductionBatchViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy',
    }), name='batch-detail'),

    # ----- Consumptions (ReadOnlyModelViewSet) -----
    path('consumptions/', views.ProductionConsumptionViewSet.as_view({'get': 'list'}),
         name='consumption-list'),
    path('consumptions/<int:pk>/',
         views.ProductionConsumptionViewSet.as_view({'get': 'retrieve'}),
         name='consumption-detail'),

    # ----- Outputs (ReadOnlyModelViewSet) -----
    path('outputs/', views.ProductionOutputViewSet.as_view({'get': 'list'}),
         name='output-list'),
    path('outputs/<int:pk>/',
         views.ProductionOutputViewSet.as_view({'get': 'retrieve'}),
         name='output-detail'),
]
