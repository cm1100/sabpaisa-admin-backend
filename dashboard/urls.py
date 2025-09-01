"""
Dashboard URL Configuration
Following Django URL patterns best practices
"""
from django.urls import path
from .views import (
    DashboardMetricsView,
    HourlyVolumeChartView,
    PaymentModeDistributionView,
    TopClientsView,
    LiveTransactionFeedView,
    ClientStatsView,
    SystemHealthView,
    RefreshMetricsView
)

app_name = 'dashboard'

urlpatterns = [
    # Main dashboard metrics
    path('dashboard/metrics/', DashboardMetricsView.as_view(), name='dashboard-metrics'),
    
    # Chart data endpoints
    path('dashboard/charts/hourly/', HourlyVolumeChartView.as_view(), name='hourly-volume'),
    path('dashboard/charts/payment-modes/', PaymentModeDistributionView.as_view(), name='payment-modes'),
    path('dashboard/charts/top-clients/', TopClientsView.as_view(), name='top-clients'),
    
    # Live feed
    path('dashboard/live-feed/', LiveTransactionFeedView.as_view(), name='live-feed'),
    
    # Statistics
    path('dashboard/client-stats/', ClientStatsView.as_view(), name='client-stats'),
    
    # System health
    path('dashboard/health/', SystemHealthView.as_view(), name='system-health'),
    
    # Cache management
    path('dashboard/refresh/', RefreshMetricsView.as_view(), name='refresh-metrics'),
]