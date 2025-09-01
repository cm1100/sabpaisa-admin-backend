from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WebhookConfigViewSet, WebhookLogsViewSet, 
    WebhookEventQueueViewSet, WebhookTemplateViewSet,
    GatewayWebhookLogsViewSet
)

router = DefaultRouter()
router.register(r'configs', WebhookConfigViewSet, basename='webhook-config')
router.register(r'logs', WebhookLogsViewSet, basename='webhook-logs')
router.register(r'event-queue', WebhookEventQueueViewSet, basename='webhook-event-queue')
router.register(r'templates', WebhookTemplateViewSet, basename='webhook-template')
router.register(r'gateway-logs', GatewayWebhookLogsViewSet, basename='gateway-webhook-logs')

urlpatterns = [
    path('', include(router.urls)),
]