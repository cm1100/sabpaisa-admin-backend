"""
Health check endpoint for AWS App Runner
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
import json

@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """
    Health check endpoint for App Runner and load balancers
    Returns 200 if service is healthy, 503 if not
    """
    try:
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            
        return JsonResponse({
            'status': 'healthy',
            'service': 'sabpaisa-admin-api',
            'database': 'connected',
            'timestamp': '2025-09-01'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'service': 'sabpaisa-admin-api', 
            'database': 'disconnected',
            'error': str(e),
            'timestamp': '2025-09-01'
        }, status=503)