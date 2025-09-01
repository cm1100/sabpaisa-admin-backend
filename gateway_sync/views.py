from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Count, Q, Avg, Sum, Max
from django.db import transaction, models
from datetime import timedelta
import logging

from .models import GatewaySyncQueue, GatewayConfiguration, GatewaySyncLog, GatewayWebhookLog, TransactionDetail
from .serializers import (
    GatewaySyncQueueSerializer, GatewayConfigurationSerializer,
    GatewaySyncLogSerializer, GatewayWebhookLogSerializer
)
from .tasks import queue_status_check, queue_refund_status_check, sync_transaction_status

logger = logging.getLogger('apps')


class GatewaySyncQueueViewSet(viewsets.ModelViewSet):
    """API for managing gateway sync queue"""
    queryset = GatewaySyncQueue.objects.all().order_by('-created_at')
    serializer_class = GatewaySyncQueueSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'sync_type', 'priority']
    search_fields = ['txn_id', 'pg_txn_id']
    ordering_fields = ['created_at', 'priority', 'attempts']
    
    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """Manually retry a sync operation"""
        sync_item = self.get_object()
        
        if sync_item.status not in ['FAILED', 'COMPLETED']:
            return Response({
                'error': 'Can only retry failed or completed sync operations'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Reset for retry
        sync_item.status = 'PENDING'
        sync_item.next_retry_at = None
        sync_item.error_message = None
        sync_item.save()
        
        return Response({
            'message': 'Sync operation queued for retry',
            'sync_id': sync_item.sync_id,
            'status': sync_item.status
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get queue statistics"""
        stats = GatewaySyncQueue.objects.aggregate(
            total=Count('sync_id'),
            pending=Count('sync_id', filter=Q(status='PENDING')),
            processing=Count('sync_id', filter=Q(status='PROCESSING')),
            completed=Count('sync_id', filter=Q(status='COMPLETED')),
            failed=Count('sync_id', filter=Q(status='FAILED')),
            avg_attempts=Avg('attempts')
        )
        
        # Recent activity (last hour)
        recent_cutoff = timezone.now() - timedelta(hours=1)
        recent_stats = GatewaySyncQueue.objects.filter(
            created_at__gte=recent_cutoff
        ).aggregate(
            recent_total=Count('sync_id'),
            recent_completed=Count('sync_id', filter=Q(status='COMPLETED')),
            recent_failed=Count('sync_id', filter=Q(status='FAILED'))
        )
        
        stats.update(recent_stats)
        return Response(stats)


class GatewayConfigurationViewSet(viewsets.ModelViewSet):
    """API for managing gateway configurations"""
    queryset = GatewayConfiguration.objects.all().order_by('gateway_name')
    serializer_class = GatewayConfigurationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['is_active', 'supports_webhook']
    search_fields = ['gateway_name', 'gateway_code']
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Test gateway connection"""
        gateway_config = self.get_object()
        
        try:
            import requests
            response = requests.get(
                gateway_config.api_endpoint,
                timeout=gateway_config.timeout_seconds,
                headers={'Authorization': f'Bearer {gateway_config.api_key}'}
            )
            
            return Response({
                'status': 'success' if response.status_code == 200 else 'failed',
                'response_code': response.status_code,
                'response_time_ms': response.elapsed.total_seconds() * 1000,
                'message': f'Connection test {"successful" if response.status_code == 200 else "failed"}'
            })
            
        except Exception as e:
            return Response({
                'status': 'failed',
                'error': str(e),
                'message': 'Connection test failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GatewaySyncLogViewSet(viewsets.ReadOnlyModelViewSet):
    """API for viewing gateway sync logs"""
    queryset = GatewaySyncLog.objects.all().order_by('-created_at')
    serializer_class = GatewaySyncLogSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['success', 'operation']
    search_fields = ['sync_queue_id']
    
    @action(detail=False, methods=['get'])
    def performance_stats(self, request):
        """Get performance statistics"""
        recent_cutoff = timezone.now() - timedelta(hours=24)
        
        stats = GatewaySyncLog.objects.filter(
            created_at__gte=recent_cutoff
        ).aggregate(
            total_requests=Count('log_id'),
            successful_requests=Count('log_id', filter=Q(success=True)),
            avg_response_time=Avg('response_time_ms'),
            max_response_time=Max('response_time_ms')
        )
        
        # Calculate success rate
        success_rate = 0
        if stats['total_requests'] > 0:
            success_rate = (stats['successful_requests'] / stats['total_requests']) * 100
        
        stats['success_rate_percent'] = round(success_rate, 2)
        
        return Response(stats)


class GatewayWebhookLogViewSet(viewsets.ReadOnlyModelViewSet):
    """API for viewing gateway webhook logs"""
    queryset = GatewayWebhookLog.objects.all().order_by('-created_at')
    serializer_class = GatewayWebhookLogSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['gateway_code', 'webhook_type', 'signature_valid', 'processed']
    search_fields = ['txn_id', 'pg_txn_id', 'ip_address']


class SyncTransactionStatusView(APIView):
    """API to manually trigger transaction status sync"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, txn_id):
        try:
            force = request.data.get('force', False)
            
            # Trigger immediate sync
            result = sync_transaction_status.delay(txn_id, force=force)
            
            return Response({
                'message': 'Transaction sync initiated',
                'txn_id': txn_id,
                'task_id': result.id,
                'force': force,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error initiating sync for {txn_id}: {str(e)}")
            return Response({
                'error': str(e),
                'txn_id': txn_id
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SyncRefundStatusView(APIView):
    """API to manually trigger refund status sync"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, txn_id):
        try:
            priority = request.data.get('priority', 1)
            pg_txn_id = request.data.get('pg_txn_id')
            
            # Queue refund status check
            result = queue_refund_status_check.delay(txn_id, pg_txn_id, priority)
            
            return Response({
                'message': 'Refund status sync queued',
                'txn_id': txn_id,
                'task_id': result.id,
                'priority': priority,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error queuing refund sync for {txn_id}: {str(e)}")
            return Response({
                'error': str(e),
                'txn_id': txn_id
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SyncSettlementStatusView(APIView):
    """API to manually trigger settlement status sync"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, txn_id):
        try:
            priority = request.data.get('priority', 2)
            
            # Create settlement sync queue entry
            sync_item = GatewaySyncQueue.objects.create(
                txn_id=txn_id,
                sync_type='SETTLEMENT_STATUS',
                priority=priority,
                request_data={'manual_trigger': True}
            )
            
            return Response({
                'message': 'Settlement status sync queued',
                'txn_id': txn_id,
                'sync_id': sync_item.sync_id,
                'priority': priority,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error queuing settlement sync for {txn_id}: {str(e)}")
            return Response({
                'error': str(e),
                'txn_id': txn_id
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SyncQueueStatsView(APIView):
    """API for comprehensive sync queue statistics"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            now = timezone.now()
            
            # Overall stats
            overall_stats = GatewaySyncQueue.objects.aggregate(
                total_items=Count('sync_id'),
                pending_items=Count('sync_id', filter=Q(status='PENDING')),
                processing_items=Count('sync_id', filter=Q(status='PROCESSING')),
                completed_items=Count('sync_id', filter=Q(status='COMPLETED')),
                failed_items=Count('sync_id', filter=Q(status='FAILED')),
                avg_attempts=Avg('attempts')
            )
            
            # Performance stats (last 24 hours)
            recent_cutoff = now - timedelta(hours=24)
            recent_logs = GatewaySyncLog.objects.filter(created_at__gte=recent_cutoff)
            
            performance_stats = recent_logs.aggregate(
                total_operations=Count('log_id'),
                successful_operations=Count('log_id', filter=Q(success=True)),
                avg_response_time=Avg('response_time_ms'),
                max_response_time=Max('response_time_ms')
            )
            
            # Calculate metrics
            success_rate = 0
            if performance_stats['total_operations'] > 0:
                success_rate = (performance_stats['successful_operations'] / performance_stats['total_operations']) * 100
            
            performance_stats['success_rate_percent'] = round(success_rate, 2)
            
            # Priority breakdown
            priority_stats = GatewaySyncQueue.objects.values('priority').annotate(
                count=Count('sync_id'),
                pending=Count('sync_id', filter=Q(status='PENDING')),
                failed=Count('sync_id', filter=Q(status='FAILED'))
            ).order_by('priority')
            
            # Type breakdown
            type_stats = GatewaySyncQueue.objects.values('sync_type').annotate(
                count=Count('sync_id'),
                pending=Count('sync_id', filter=Q(status='PENDING')),
                completed=Count('sync_id', filter=Q(status='COMPLETED')),
                failed=Count('sync_id', filter=Q(status='FAILED'))
            )
            
            return Response({
                'overall_stats': overall_stats,
                'performance_stats': performance_stats,
                'priority_breakdown': list(priority_stats),
                'type_breakdown': list(type_stats),
                'timestamp': now.isoformat(),
                'sla_target': '30 seconds',
                'current_avg_response_time': performance_stats.get('avg_response_time', 0)
            })
            
        except Exception as e:
            logger.error(f"Error generating sync queue stats: {str(e)}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SyncDashboardView(APIView):
    """Comprehensive dashboard view for gateway sync monitoring"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            now = timezone.now()
            
            # Time-based filters
            last_hour = now - timedelta(hours=1)
            last_24h = now - timedelta(hours=24)
            last_7d = now - timedelta(days=7)
            
            # Recent activity
            recent_activity = {
                'last_hour': GatewaySyncQueue.objects.filter(created_at__gte=last_hour).count(),
                'last_24_hours': GatewaySyncQueue.objects.filter(created_at__gte=last_24h).count(),
                'last_7_days': GatewaySyncQueue.objects.filter(created_at__gte=last_7d).count()
            }
            
            # Current queue status
            queue_status = {
                'pending': GatewaySyncQueue.objects.filter(status='PENDING').count(),
                'processing': GatewaySyncQueue.objects.filter(status='PROCESSING').count(),
                'failed_ready_for_retry': GatewaySyncQueue.objects.filter(
                    status='FAILED',
                    next_retry_at__lte=now,
                    attempts__lt=models.F('max_attempts')
                ).count()
            }
            
            # Performance metrics
            recent_logs = GatewaySyncLog.objects.filter(created_at__gte=last_24h)
            performance = {
                'total_operations_24h': recent_logs.count(),
                'success_rate_24h': 0,
                'avg_response_time_24h': 0,
                'sla_compliance': 0  # Percentage under 30 seconds
            }
            
            if recent_logs.exists():
                successful_ops = recent_logs.filter(success=True).count()
                performance['success_rate_24h'] = round((successful_ops / recent_logs.count()) * 100, 2)
                
                avg_time = recent_logs.aggregate(avg=Avg('response_time_ms'))['avg']
                performance['avg_response_time_24h'] = round(avg_time or 0, 2)
                
                # SLA compliance (under 30 seconds = 30000ms)
                under_sla = recent_logs.filter(response_time_ms__lt=30000).count()
                performance['sla_compliance'] = round((under_sla / recent_logs.count()) * 100, 2)
            
            # Gateway breakdown
            gateway_stats = GatewaySyncQueue.objects.values(
                'sync_type'
            ).annotate(
                total=Count('sync_id'),
                pending=Count('sync_id', filter=Q(status='PENDING')),
                failed=Count('sync_id', filter=Q(status='FAILED'))
            )
            
            # Recent errors
            recent_errors = GatewaySyncQueue.objects.filter(
                status='FAILED',
                updated_at__gte=last_hour
            ).values('error_message', 'sync_type').annotate(
                count=Count('sync_id')
            ).order_by('-count')[:5]
            
            # Webhook activity
            webhook_stats = GatewayWebhookLog.objects.filter(
                created_at__gte=last_24h
            ).aggregate(
                total_webhooks=Count('log_id'),
                valid_signatures=Count('log_id', filter=Q(signature_valid=True)),
                processed_webhooks=Count('log_id', filter=Q(processed=True))
            )
            
            return Response({
                'recent_activity': recent_activity,
                'queue_status': queue_status,
                'performance': performance,
                'gateway_stats': list(gateway_stats),
                'recent_errors': list(recent_errors),
                'webhook_stats': webhook_stats,
                'timestamp': now.isoformat(),
                'system_health': 'healthy' if queue_status['processing'] < 100 else 'degraded'
            })
            
        except Exception as e:
            logger.error(f"Error generating sync dashboard: {str(e)}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
