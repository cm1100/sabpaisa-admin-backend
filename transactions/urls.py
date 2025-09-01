"""
Transaction URL Configuration
Following Django URL patterns best practices
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TransactionViewSet,
    RefundView,
    RefundApprovalView,
    DisputeView,
    TransactionAnalyticsView,
    SettlementSummaryView,
    PendingSettlementsView,
    SettledTransactionsView,
    ProcessBatchSettlementView,
    ClientSettlementSummaryView,
    ExportPendingSettlementsView
)

app_name = 'transactions'

# Create router for viewsets
router = DefaultRouter()
router.register(r'', TransactionViewSet, basename='transaction')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Refund endpoints
    path('refunds/', RefundView.as_view(), name='refunds'),
    path('refunds/<str:refund_id>/approve/', RefundApprovalView.as_view(), name='refund-approve'),
    
    # Dispute endpoints
    path('disputes/', DisputeView.as_view(), name='disputes'),
    
    # Analytics endpoints
    path('analytics/', TransactionAnalyticsView.as_view(), name='analytics'),
    
    # Settlement endpoints
    path('settlements/', SettlementSummaryView.as_view(), name='settlement-summary'),
    path('settlements/pending/', PendingSettlementsView.as_view(), name='pending-settlements'),
    path('settlements/settled/', SettledTransactionsView.as_view(), name='settled-transactions'),
    path('settlements/process-batch/', ProcessBatchSettlementView.as_view(), name='process-batch-settlement'),
    path('settlements/client-summary/', ClientSettlementSummaryView.as_view(), name='client-settlement-summary'),
    path('settlements/export-pending/', ExportPendingSettlementsView.as_view(), name='export-pending-settlements'),
]