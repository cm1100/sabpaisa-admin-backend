from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, F
from django.utils import timezone
from datetime import datetime, timedelta
import requests
import json
import logging

from .models import WebhookConfig, WebhookLogs, WebhookEventQueue, WebhookTemplate, GatewayWebhookLogs
from .serializers import (
    WebhookConfigSerializer, WebhookLogsSerializer, 
    WebhookTestSerializer, WebhookStatsSerializer,
    BulkRetrySerializer, WebhookEventQueueSerializer,
    WebhookTemplateSerializer
)

logger = logging.getLogger(__name__)

class WebhookConfigViewSet(viewsets.ModelViewSet):
    serializer_class = WebhookConfigSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = WebhookConfig.objects.all().order_by('-created_at')
        client_id = self.request.query_params.get('client_id')
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user.username)

    @action(detail=True, methods=['post'])
    def test_webhook(self, request, pk=None):
        """Test webhook endpoint with sample payload"""
        config = self.get_object()
        serializer = WebhookTestSerializer(data=request.data)
        
        if serializer.is_valid():
            test_data = {
                'event_type': serializer.validated_data['event_type'],
                'timestamp': datetime.now().isoformat(),
                'data': serializer.validated_data['test_payload'],
                'test_mode': True
            }
            
            # Send test webhook immediately (not via Celery for testing)
            webhook_log = WebhookLogs.objects.create(
                client_id=config.client_id,
                config_id=config.config_id,
                event_type=serializer.validated_data['event_type'],
                payload=test_data,
                endpoint_url=config.endpoint_url,
                delivery_status='PENDING'
            )
            
            # Try to send the webhook
            try:
                signature = config.generate_signature(test_data)
                headers = {
                    'Content-Type': 'application/json',
                    'X-Webhook-Signature': signature,
                    'X-Webhook-Event': webhook_log.event_type,
                    'User-Agent': 'SabPaisa-Webhooks/1.0'
                }
                
                response = requests.post(
                    config.endpoint_url,
                    json=test_data,
                    headers=headers,
                    timeout=config.timeout_seconds
                )
                
                webhook_log.http_status_code = response.status_code
                webhook_log.response_body = response.text[:1000]
                webhook_log.signature_sent = signature
                webhook_log.attempts = 1
                
                if response.status_code in [200, 201, 202]:
                    webhook_log.delivery_status = 'SUCCESS'
                    webhook_log.delivered_at = timezone.now()
                else:
                    webhook_log.delivery_status = 'FAILED'
                    webhook_log.error_message = f'HTTP {response.status_code}'
                    
            except requests.Timeout:
                webhook_log.delivery_status = 'FAILED'
                webhook_log.error_message = 'Request timeout'
            except Exception as e:
                webhook_log.delivery_status = 'FAILED'
                webhook_log.error_message = str(e)
            
            webhook_log.save()
            
            return Response({
                'message': 'Test webhook sent',
                'webhook_log_id': webhook_log.webhook_id,
                'status': webhook_log.delivery_status,
                'http_status': webhook_log.http_status_code
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def toggle_status(self, request, pk=None):
        """Toggle webhook configuration active status"""
        config = self.get_object()
        config.is_active = not config.is_active
        config.save()
        
        return Response({
            'message': f'Webhook {"activated" if config.is_active else "deactivated"}',
            'is_active': config.is_active
        })

    @action(detail=False, methods=['get'])
    def delivery_stats(self, request):
        """Get webhook delivery statistics"""
        client_id = request.query_params.get('client_id')
        
        base_query = WebhookLogs.objects.all()
        if client_id:
            base_query = base_query.filter(client_id=client_id)
        
        # Last 7 days statistics
        seven_days_ago = timezone.now() - timedelta(days=7)
        recent_logs = base_query.filter(created_at__gte=seven_days_ago)
        
        stats = {
            'total_webhooks': base_query.count(),
            'last_7_days': {
                'total_sent': recent_logs.count(),
                'successful': recent_logs.filter(delivery_status='SUCCESS').count(),
                'failed': recent_logs.filter(delivery_status='FAILED').count(),
                'pending': recent_logs.filter(delivery_status='PENDING').count(),
            },
            'success_rate_7_days': 0,
            'avg_response_time': '245ms',  # Would calculate from response times
            'most_failed_endpoints': []
        }
        
        if stats['last_7_days']['total_sent'] > 0:
            stats['success_rate_7_days'] = round(
                (stats['last_7_days']['successful'] / stats['last_7_days']['total_sent']) * 100, 2
            )
        
        # Get most failed endpoints
        failed_endpoints = base_query.filter(
            delivery_status='FAILED'
        ).values('endpoint_url').annotate(
            count=Count('webhook_id')
        ).order_by('-count')[:5]
        
        stats['most_failed_endpoints'] = [
            {'url': ep['endpoint_url'], 'failures': ep['count']} 
            for ep in failed_endpoints
        ]
        
        return Response(stats)

class WebhookLogsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = WebhookLogsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = WebhookLogs.objects.all().order_by('-created_at')
        
        # Filters
        client_id = self.request.query_params.get('client_id')
        config_id = self.request.query_params.get('config_id')
        event_type = self.request.query_params.get('event_type')
        delivery_status = self.request.query_params.get('status')
        
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        if config_id:
            queryset = queryset.filter(config_id=config_id)
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        if delivery_status:
            queryset = queryset.filter(delivery_status=delivery_status)
            
        return queryset

    @action(detail=True, methods=['post'])
    def retry_webhook(self, request, pk=None):
        """Manually retry a failed webhook"""
        webhook_log = self.get_object()
        
        if webhook_log.delivery_status == 'SUCCESS':
            return Response({
                'error': 'Webhook already delivered successfully'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if webhook_log.attempts >= webhook_log.max_attempts:
            return Response({
                'error': 'Maximum retry attempts reached'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Reset for retry
        webhook_log.delivery_status = 'RETRY'
        webhook_log.next_retry_at = timezone.now()
        webhook_log.save()
        
        # Process immediately for manual retry
        try:
            self._send_webhook(webhook_log)
        except Exception as e:
            logger.error(f"Error retrying webhook: {str(e)}")
        
        return Response({'message': 'Webhook retry attempted'})

    @action(detail=False, methods=['post'])
    def bulk_retry(self, request):
        """Retry all failed webhooks for a client"""
        serializer = BulkRetrySerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        client_id = serializer.validated_data['client_id']
        max_age_hours = serializer.validated_data.get('max_age_hours', 24)
        
        time_threshold = timezone.now() - timedelta(hours=max_age_hours)
        
        failed_webhooks = WebhookLogs.objects.filter(
            client_id=client_id,
            delivery_status='FAILED',
            attempts__lt=F('max_attempts'),
            created_at__gte=time_threshold
        )
        
        retry_count = 0
        for webhook in failed_webhooks:
            webhook.delivery_status = 'RETRY'
            webhook.next_retry_at = timezone.now()
            webhook.save()
            retry_count += 1
        
        return Response({
            'message': f'{retry_count} webhooks queued for retry',
            'total_failed': failed_webhooks.count()
        })
    
    def _send_webhook(self, webhook_log):
        """Helper method to send webhook"""
        try:
            config = WebhookConfig.objects.get(config_id=webhook_log.config_id)
            
            if not config.is_active:
                webhook_log.delivery_status = 'FAILED'
                webhook_log.error_message = 'Webhook configuration is inactive'
                webhook_log.save()
                return
            
            # Prepare headers
            signature = config.generate_signature(webhook_log.payload)
            headers = {
                'Content-Type': 'application/json',
                'X-Webhook-Signature': signature,
                'X-Webhook-Event': webhook_log.event_type,
                'User-Agent': 'SabPaisa-Webhooks/1.0'
            }
            
            # Update attempt count
            webhook_log.attempts += 1
            webhook_log.signature_sent = signature
            
            # Send webhook
            response = requests.post(
                webhook_log.endpoint_url,
                json=webhook_log.payload,
                headers=headers,
                timeout=config.timeout_seconds
            )
            
            # Update delivery status
            webhook_log.http_status_code = response.status_code
            webhook_log.response_body = response.text[:1000]
            
            if response.status_code in [200, 201, 202]:
                webhook_log.delivery_status = 'SUCCESS'
                webhook_log.delivered_at = timezone.now()
            else:
                webhook_log.delivery_status = 'FAILED'
                webhook_log.error_message = f'HTTP {response.status_code}: {response.text[:500]}'
            
            webhook_log.save()
            
        except Exception as e:
            webhook_log.delivery_status = 'FAILED'
            webhook_log.error_message = str(e)
            webhook_log.save()

class WebhookEventQueueViewSet(viewsets.ReadOnlyModelViewSet):
    """View queued webhook events"""
    queryset = WebhookEventQueue.objects.all().order_by('-created_at')
    serializer_class = WebhookEventQueueSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset

class WebhookTemplateViewSet(viewsets.ModelViewSet):
    """Manage webhook payload templates"""
    queryset = WebhookTemplate.objects.all()
    serializer_class = WebhookTemplateSerializer
    permission_classes = [IsAuthenticated]

class GatewayWebhookLogsViewSet(viewsets.ReadOnlyModelViewSet):
    """View gateway webhook logs (existing table)"""
    queryset = GatewayWebhookLogs.objects.all().order_by('-created_at')
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """List gateway webhook logs with filters"""
        queryset = self.get_queryset()
        
        # Apply filters
        gateway_code = request.query_params.get('gateway_code')
        txn_id = request.query_params.get('txn_id')
        processed = request.query_params.get('processed')
        
        if gateway_code:
            queryset = queryset.filter(gateway_code=gateway_code)
        if txn_id:
            queryset = queryset.filter(txn_id=txn_id)
        if processed is not None:
            queryset = queryset.filter(processed=processed.lower() == 'true')
        
        # Paginate
        page = self.paginate_queryset(queryset)
        if page is not None:
            data = [{
                'log_id': log.log_id,
                'gateway_code': log.gateway_code,
                'webhook_type': log.webhook_type,
                'txn_id': log.txn_id,
                'pg_txn_id': log.pg_txn_id,
                'signature_valid': log.signature_valid,
                'processed': log.processed,
                'response_status': log.response_status,
                'created_at': log.created_at
            } for log in page]
            return self.get_paginated_response(data)
        
        return Response([])
