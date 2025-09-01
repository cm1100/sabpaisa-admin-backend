from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .webhook_handlers import GatewayWebhookView, webhook_health_check

router = DefaultRouter()
router.register(r'queue', views.GatewaySyncQueueViewSet)
router.register(r'configurations', views.GatewayConfigurationViewSet)
router.register(r'logs', views.GatewaySyncLogViewSet)
router.register(r'webhook-logs', views.GatewayWebhookLogViewSet)

app_name = 'gateway_sync'

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    
    # Sync operations
    path('api/sync/status/<str:txn_id>/', views.SyncTransactionStatusView.as_view(), name='sync-status'),
    path('api/sync/refund/<str:txn_id>/', views.SyncRefundStatusView.as_view(), name='sync-refund'),
    path('api/sync/settlement/<str:txn_id>/', views.SyncSettlementStatusView.as_view(), name='sync-settlement'),
    path('api/sync/queue/stats/', views.SyncQueueStatsView.as_view(), name='queue-stats'),
    path('api/sync/dashboard/', views.SyncDashboardView.as_view(), name='sync-dashboard'),
    
    # Webhook endpoints
    path('webhooks/<str:gateway_code>/', GatewayWebhookView.as_view(), name='gateway-webhook'),
    path('webhooks/health/', webhook_health_check, name='webhook-health'),
]