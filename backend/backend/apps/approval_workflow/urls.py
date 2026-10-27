"""
Approval Workflow URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'approval_workflow'

router = DefaultRouter()
router.register(r'queue', views.ApprovalQueueViewSet, basename='approval')
router.register(r'rules', views.ApprovalRuleViewSet, basename='rule')

urlpatterns = [
    path('queue/pending/', views.ApprovalQueueViewSet.as_view({'get': 'pending'}),
         name='pending'),
    path('queue/pending_count/', views.ApprovalQueueViewSet.as_view({'get': 'pending_count'}),
         name='pending-count'),
    path('queue/<int:pk>/decide/', views.ApprovalQueueViewSet.as_view({'post': 'decide'}),
         name='decide'),
] + router.urls
