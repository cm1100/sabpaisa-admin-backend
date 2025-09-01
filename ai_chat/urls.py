"""
AI Chat URL Configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AIChatViewSet

router = DefaultRouter()
router.register(r'sessions', AIChatViewSet, basename='ai-chat-session')
# router.register(r'audit', AIActionAuditViewSet, basename='ai-action-audit')  # Commented out - missing in views

urlpatterns = [
    path('', include(router.urls)),
]