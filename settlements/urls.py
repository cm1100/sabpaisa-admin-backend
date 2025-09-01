"""
Settlement URL Configuration
Following Django URL patterns best practices
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SettlementBatchViewSet,
    SettlementConfigurationViewSet,
    SettlementReportView,
    SettlementReconciliationView,
    ReconciliationUpdateView,
    SettlementAnalyticsView,
    SettlementExportView,
    SettlementActivityView,
    SettlementCycleDistributionView,
    BankWisePerformanceView,
    SettlementDisputesView
)

app_name = 'settlements'

# Create router for viewsets
router = DefaultRouter()
router.register(r'batches', SettlementBatchViewSet, basename='settlement-batch')
router.register(r'configurations', SettlementConfigurationViewSet, basename='settlement-config')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Report endpoints
    path('reports/', SettlementReportView.as_view(), name='settlement-reports'),
    
    # Reconciliation endpoints
    path('reconciliations/', SettlementReconciliationView.as_view(), name='reconciliations'),
    path('reconciliations/<str:reconciliation_id>/', ReconciliationUpdateView.as_view(), name='reconciliation-update'),
    
    # Analytics endpoints
    path('analytics/', SettlementAnalyticsView.as_view(), name='settlement-analytics'),
    path('analytics/cycle-distribution/', SettlementCycleDistributionView.as_view(), name='settlement-cycle-distribution'),
    path('activity/', SettlementActivityView.as_view(), name='settlement-activity'),
    
    # Export endpoints
    path('export/', SettlementExportView.as_view(), name='settlement-export'),
    
    # Bank-wise performance endpoint
    path('bank-wise-performance/', BankWisePerformanceView.as_view(), name='bank-wise-performance'),
    
    # Disputes endpoints
    path('disputes/', SettlementDisputesView.as_view(), name='settlement-disputes'),
]