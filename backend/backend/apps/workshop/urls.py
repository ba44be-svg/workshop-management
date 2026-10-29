"""
Workshop URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'workshop'

router = DefaultRouter()
router.register(r'contractors', views.ContractorViewSet, basename='contractor')
router.register(r'employees', views.EmployeeViewSet, basename='employee')
router.register(r'purchases', views.PurchaseViewSet, basename='purchase')
router.register(r'purchase-returns', views.PurchaseReturnViewSet, basename='purchase-return')
router.register(r'issues', views.WorkshopIssueViewSet, basename='issue')
router.register(r'returns', views.WorkshopReturnViewSet, basename='return')

urlpatterns = [
    # Custom actions (تعریف شده قبل از router.urls برای اولویت تطبیق)
    path('purchases/create_purchase/', views.PurchaseViewSet.as_view({'post': 'create_purchase'}),
         name='create-purchase'),
    path('purchase-returns/create_return/', views.PurchaseReturnViewSet.as_view({'post': 'create_return'}),
         name='create-purchase-return'),
    path('issues/create_issue/', views.WorkshopIssueViewSet.as_view({'post': 'create_issue'}),
         name='create-issue'),
    path('returns/create_return/', views.WorkshopReturnViewSet.as_view({'post': 'create_return'}),
         name='create-return'),
] + router.urls
