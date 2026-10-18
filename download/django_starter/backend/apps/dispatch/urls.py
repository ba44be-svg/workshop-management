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
] + router.urls
