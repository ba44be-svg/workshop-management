"""
Dispatch URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'dispatch'

router = DefaultRouter()
router.register(r'vehicles', views.VehicleViewSet, basename='vehicle')
router.register(r'routes', views.RouteViewSet, basename='route')
router.register(r'', views.DispatchHeaderViewSet, basename='dispatch')
router.register(r'lines', views.DispatchLineViewSet, basename='dispatch-line')
router.register(r'visits', views.SalespersonVisitViewSet, basename='visit')

urlpatterns = [
    path('create/', views.DispatchHeaderViewSet.as_view({'post': 'create_dispatch'}),
         name='create-dispatch'),
    path('<int:pk>/start_delivery/',
         views.DispatchHeaderViewSet.as_view({'post': 'start_delivery'}),
         name='start-delivery'),
    path('<int:pk>/mark_arrived/',
         views.DispatchHeaderViewSet.as_view({'post': 'mark_arrived'}),
         name='mark-arrived'),
    path('<int:pk>/cancel/',
         views.DispatchHeaderViewSet.as_view({'post': 'cancel'}),
         name='cancel-dispatch'),
    # D02 — تحویل به عوامل پخش
    path('settlement_check/',
         views.DispatchHeaderViewSet.as_view({'get': 'settlement_check'}),
         name='settlement-check'),
    path('distributor_summary/',
         views.DispatchHeaderViewSet.as_view({'get': 'distributor_summary'}),
         name='distributor-summary'),
    path('distributor_detail/',
         views.DispatchHeaderViewSet.as_view({'get': 'distributor_detail'}),
         name='distributor-detail'),
    path('distributor_commission/',
         views.DispatchHeaderViewSet.as_view({'get': 'distributor_commission'}),
         name='distributor-commission'),
    path('my_dispatches/',
         views.DispatchHeaderViewSet.as_view({'get': 'my_dispatches'}),
         name='my-dispatches'),
] + router.urls
