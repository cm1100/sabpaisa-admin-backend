"""
URL configuration for sabpaisa_admin project.
Following SOLID principles with clear separation of concerns
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API Endpoints
    # Explicit export aliases for clients and transactions
    path('api/clients/export/', __import__('clients.export_view', fromlist=['ExportClientsView']).ExportClientsView.as_view(), name='clients-export'),
    path('api/clients/export', __import__('clients.export_view', fromlist=['ExportClientsView']).ExportClientsView.as_view(), name='clients-export-no-slash'),
    path('api/export/clients/', __import__('clients.export_view', fromlist=['ExportClientsView']).ExportClientsView.as_view(), name='clients-export-alt'),
    # Regex fallback to catch any missing trailing slash variants
    re_path(r'^api/clients/export/?$', __import__('clients.export_view', fromlist=['ExportClientsView']).ExportClientsView.as_view()),

    path('api/transactions/export/', __import__('transactions.export_view', fromlist=['ExportTransactionsView']).ExportTransactionsView.as_view(), name='transactions-export'),
    path('api/transactions/export', __import__('transactions.export_view', fromlist=['ExportTransactionsView']).ExportTransactionsView.as_view(), name='transactions-export-no-slash'),
    path('api/export/transactions/', __import__('transactions.export_view', fromlist=['ExportTransactionsView']).ExportTransactionsView.as_view(), name='transactions-export-alt'),
    re_path(r'^api/transactions/export/?$', __import__('transactions.export_view', fromlist=['ExportTransactionsView']).ExportTransactionsView.as_view()),

    # NEW: Dedicated, collision‑free download endpoints (v2)
    # These avoid any router or lookup conflicts entirely
    path('api/downloads/clients/', __import__('clients.export_view', fromlist=['ExportClientsView']).ExportClientsView.as_view(), name='clients-export-downloads'),
    re_path(r'^api/downloads/clients/?$', __import__('clients.export_view', fromlist=['ExportClientsView']).ExportClientsView.as_view()),

    path('api/downloads/transactions/', __import__('transactions.export_view', fromlist=['ExportTransactionsView']).ExportTransactionsView.as_view(), name='transactions-export-downloads'),
    re_path(r'^api/downloads/transactions/?$', __import__('transactions.export_view', fromlist=['ExportTransactionsView']).ExportTransactionsView.as_view()),
    path('api/', include('authentication.urls')),
    path('api/', include('clients.urls')),
    path('api/', include('dashboard.urls')),
    path('api/transactions/', include('transactions.urls')),
    path('api/settlements/', include('settlements.urls')),
    path('api/gateway-sync/', include('gateway_sync.urls')),
    path('api/', include('compliance.urls')),
    path('api/reports/', include('reports.urls')),
    path('api/integration/', include('integration.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/administration/', include('administration.urls')),
    path('api/', include('reconciliation.urls')),
    path('api/', include('refunds.urls')),
    path('api/webhooks/', include('webhooks.urls')),
    path('api/fees/', include('fees.urls')),
    path('api/ai-chat/', include('ai_chat.urls')),  # AI Chat Assistant
    path('api/ai-builder/', include('ai_builder.urls')),  # AI Dashboard Builder Agent
    path('api/productivity/', include('productivity.urls')),
    path('api/routing/', include('routing.urls')),
    path('api/audits/', include('audits.urls')),
    path('', include('zones.urls')),
    
    # Health Check for App Runner
    path('api/health/', __import__('health_check').health_check, name='health_check'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
