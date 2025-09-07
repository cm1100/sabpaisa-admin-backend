"""
Transaction URL Configuration
Following Django URL patterns best practices
"""
from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from .views import (
    TransactionViewSet,
    RefundView,
    RefundApprovalView,
    RefundApprovalActionView,
    RefundDashboardView,
    DisputeView,
    TransactionAnalyticsView,
    SettlementSummaryView,
    PendingSettlementsView,
    SettledTransactionsView,
    ProcessBatchSettlementView,
    ClientSettlementSummaryView,
    ExportPendingSettlementsView
)
from .export_view import ExportTransactionsView

app_name = 'transactions'

# Create router for viewsets
router = DefaultRouter()
router.register(r'', TransactionViewSet, basename='transaction')

urlpatterns = [
    # Explicit export route to avoid detail lookup collisions
    path('export/', ExportTransactionsView.as_view(), name='transaction-export'),
    re_path(r'^export/?$', ExportTransactionsView.as_view()),

    # Include router URLs
    path('', include(router.urls)),
    
    # Refund endpoints
    path('refunds/', RefundView.as_view(), name='refunds'),
    # Alias for initiate to match FE expectations
    path('refunds/initiate/', RefundView.as_view(), name='refunds-initiate'),
    path('refunds/<str:refund_id>/approve/', RefundApprovalView.as_view(), name='refund-approve'),
    # Bulk approve/reject endpoint used by FE
    path('refunds/approve/', RefundApprovalActionView.as_view(), name='refund-approve-action'),
    # Refund dashboard stats
    path('refunds/dashboard/', RefundDashboardView.as_view(), name='refund-dashboard'),
    
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
