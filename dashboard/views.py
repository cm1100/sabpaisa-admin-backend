"""
Dashboard API Views
Following SOLID principles with proper separation of concerns
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.cache import cache
import logging

from .services import (
    DashboardAggregatorService,
    MetricsCalculatorService,
    ChartDataService,
    LiveFeedService,
    ClientStatsService,
    SystemHealthService
)
from .serializers import (
    DashboardMetricsSerializer,
    HourlyVolumeSerializer,
    PaymentModeDistributionSerializer,
    TopClientsSerializer,
    RecentTransactionSerializer,
    ClientStatsSerializer,
    SystemHealthSerializer
)

logger = logging.getLogger(__name__)


class DashboardMetricsView(APIView):
    """
    Main dashboard metrics endpoint
    Returns comprehensive dashboard data
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.aggregator_service = DashboardAggregatorService()
        self.metrics_service = MetricsCalculatorService()
    
    @method_decorator(cache_page(60))  # Cache for 1 minute
    def get(self, request):
        """Get all dashboard metrics"""
        try:
            # Get time range from query params
            time_range = request.query_params.get('range', '24h')
            
            # Aggregate all metrics
            metrics = self.aggregator_service.get_dashboard_metrics(time_range)
            
            # Serialize and return
            serializer = DashboardMetricsSerializer(metrics)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching dashboard metrics: {str(e)}")
            return Response(
                {"error": "Failed to fetch dashboard metrics"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class HourlyVolumeChartView(APIView):
    """
    Hourly transaction volume chart data
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.chart_service = ChartDataService()
    
    def get(self, request):
        """Get hourly volume data for charts"""
        try:
            hours = int(request.query_params.get('hours', 24))
            
            # Get chart data
            chart_data = self.chart_service.get_hourly_volume(hours)
            
            # Serialize and return
            serializer = HourlyVolumeSerializer(chart_data, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching hourly volume: {str(e)}")
            return Response(
                {"error": "Failed to fetch chart data"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PaymentModeDistributionView(APIView):
    """
    Payment mode distribution chart data
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.chart_service = ChartDataService()
    
    def get(self, request):
        """Get payment mode distribution"""
        try:
            # Get time range from query params
            time_range = request.query_params.get('range', '24h')
            
            # Get distribution data
            distribution = self.chart_service.get_payment_mode_distribution(time_range)
            
            # Serialize and return
            serializer = PaymentModeDistributionSerializer(distribution, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching payment distribution: {str(e)}")
            return Response(
                {"error": "Failed to fetch payment distribution"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TopClientsView(APIView):
    """
    Top clients by transaction volume
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.chart_service = ChartDataService()
    
    def get(self, request):
        """Get top clients data"""
        try:
            limit = int(request.query_params.get('limit', 10))
            time_range = request.query_params.get('range', '24h')
            
            # Get top clients
            top_clients = self.chart_service.get_top_clients(limit, time_range)
            
            # Serialize and return
            serializer = TopClientsSerializer(top_clients, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching top clients: {str(e)}")
            return Response(
                {"error": "Failed to fetch top clients"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LiveTransactionFeedView(APIView):
    """
    Live transaction feed for real-time monitoring
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.feed_service = LiveFeedService()
    
    def get(self, request):
        """Get recent transactions"""
        try:
            limit = int(request.query_params.get('limit', 20))
            
            # Get recent transactions
            transactions = self.feed_service.get_recent_transactions(limit)
            
            # Serialize and return
            serializer = RecentTransactionSerializer(transactions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching live feed: {str(e)}")
            return Response(
                {"error": "Failed to fetch live feed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ClientStatsView(APIView):
    """
    Client statistics and analytics
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client_service = ClientStatsService()
    
    @method_decorator(cache_page(300))  # Cache for 5 minutes
    def get(self, request):
        """Get client statistics"""
        try:
            # Get client stats
            stats = self.client_service.get_client_statistics()
            
            # Serialize and return
            serializer = ClientStatsSerializer(stats)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching client stats: {str(e)}")
            return Response(
                {"error": "Failed to fetch client statistics"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SystemHealthView(APIView):
    """
    System health monitoring endpoint
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.health_service = SystemHealthService()
    
    def get(self, request):
        """Get system health status"""
        try:
            # Get health status
            health = self.health_service.get_system_health()
            
            # Serialize and return
            serializer = SystemHealthSerializer(health)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching system health: {str(e)}")
            return Response(
                {"error": "Failed to fetch system health"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RefreshMetricsView(APIView):
    """
    Force refresh of cached metrics
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Clear cache and refresh metrics"""
        try:
            # Clear relevant cache keys
            cache.delete_many([
                'dashboard_metrics_*',
                'client_stats',
                'system_health'
            ])
            
            return Response(
                {"message": "Metrics cache cleared successfully"},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return Response(
                {"error": "Failed to clear cache"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )