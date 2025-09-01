"""
Client URL Configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClientViewSet
from .payment_config_views import (
    PaymentConfigurationViewSet,
    PaymentMethodViewSet,
    ClientPaymentMethodViewSet
)

router = DefaultRouter()
router.register(r'clients', ClientViewSet, basename='client')
router.register(r'payment-configurations', PaymentConfigurationViewSet, basename='payment-configuration')
router.register(r'payment-methods', PaymentMethodViewSet, basename='payment-method')
router.register(r'client-payment-methods', ClientPaymentMethodViewSet, basename='client-payment-method')

# The router will automatically generate URLs with client_id parameter
# due to lookup_field = 'client_id' in the viewset

urlpatterns = [
    path('', include(router.urls)),
]