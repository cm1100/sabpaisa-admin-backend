"""
URL configuration for sabpaisa_admin project.
Following SOLID principles with clear separation of concerns
"""
from django.contrib import admin
from django.urls import path, include
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
    path('api/', include('authentication.urls')),
    path('api/', include('clients.urls')),
    path('api/', include('dashboard.urls')),
    path('api/transactions/', include('transactions.urls')),
    path('api/settlements/', include('settlements.urls')),
    path('api/gateway-sync/', include('gateway_sync.urls')),
    path('api/', include('compliance.urls')),
    path('api/', include('reconciliation.urls')),
    path('api/', include('refunds.urls')),
    path('api/webhooks/', include('webhooks.urls')),
    path('api/fees/', include('fees.urls')),
    path('api/ai-chat/', include('ai_chat.urls')),  # AI Chat Assistant
    path('', include('zones.urls')),
    
    # Health Check for App Runner
    path('api/health/', __import__('health_check').health_check, name='health_check'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)