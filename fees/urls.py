from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FeeConfigurationViewSet, FeeCalculationViewSet,
    FeeCalculationLogViewSet, PromotionalFeesViewSet,
    FeeReconciliationViewSet
)

router = DefaultRouter()
router.register(r'configurations', FeeConfigurationViewSet, basename='fee-configuration')
router.register(r'calculate', FeeCalculationViewSet, basename='fee-calculation')
router.register(r'calculation-logs', FeeCalculationLogViewSet, basename='fee-calculation-log')
router.register(r'promotional', PromotionalFeesViewSet, basename='promotional-fees')
router.register(r'reconciliation', FeeReconciliationViewSet, basename='fee-reconciliation')

urlpatterns = [
    path('', include(router.urls)),
]