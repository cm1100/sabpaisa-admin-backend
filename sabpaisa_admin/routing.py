"""
WebSocket routing configuration
"""
from django.urls import re_path
from dashboard import consumers

websocket_urlpatterns = [
    re_path(r'ws/dashboard/$', consumers.DashboardConsumer.as_asgi()),
    re_path(r'ws/transactions/$', consumers.TransactionConsumer.as_asgi()),
]