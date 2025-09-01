# Simplified version without Celery dependency for now
# In production, these would be @shared_task decorated functions

from django.utils import timezone
from datetime import datetime, timedelta
import requests
import json
import logging

from .models import WebhookConfig, WebhookLogs, WebhookEventQueue

logger = logging.getLogger(__name__)

def send_webhook_notification(webhook_log_id):
    """Send webhook notification with retry logic"""
    try:
        webhook_log = WebhookLogs.objects.get(webhook_id=webhook_log_id)
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
        webhook_log.save()
        
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
            
            # Schedule retry if attempts remaining
            if webhook_log.attempts < webhook_log.max_attempts:
                delay_minutes = [5, 15, 60][min(webhook_log.attempts - 1, 2)]
                webhook_log.next_retry_at = timezone.now() + timedelta(minutes=delay_minutes)
                webhook_log.delivery_status = 'RETRY'
        
        webhook_log.save()
        
    except WebhookLogs.DoesNotExist:
        logger.error(f'Webhook log {webhook_log_id} not found')
    except requests.Timeout:
        webhook_log.delivery_status = 'FAILED'
        webhook_log.error_message = 'Request timeout'
        webhook_log.save()
    except requests.RequestException as e:
        webhook_log.delivery_status = 'FAILED'
        webhook_log.error_message = str(e)
        webhook_log.save()
    except Exception as e:
        logger.error(f'Unexpected error in webhook delivery: {str(e)}')
        if webhook_log:
            webhook_log.delivery_status = 'FAILED'
            webhook_log.error_message = f'Internal error: {str(e)}'
            webhook_log.save()

def retry_failed_webhooks():
    """Periodic task to retry failed webhooks"""
    retry_webhooks = WebhookLogs.objects.filter(
        delivery_status='RETRY',
        next_retry_at__lte=timezone.now(),
        attempts__lt=F('max_attempts')
    )
    
    logger.info(f'Found {retry_webhooks.count()} webhooks ready for retry')
    
    for webhook in retry_webhooks:
        send_webhook_notification(webhook.webhook_id)

def trigger_webhook_event(client_id, event_type, payload_data):
    """Trigger webhook notifications for an event"""
    configs = WebhookConfig.objects.filter(
        client_id=client_id,
        is_active=True,
        events_subscribed__contains=[event_type]
    )
    
    webhook_count = 0
    for config in configs:
        # Create webhook log entry
        webhook_log = WebhookLogs.objects.create(
            client_id=client_id,
            config_id=config.config_id,
            event_type=event_type,
            payload={
                'event_type': event_type,
                'timestamp': datetime.now().isoformat(),
                'data': payload_data
            },
            endpoint_url=config.endpoint_url,
            delivery_status='PENDING',
            max_attempts=config.max_retry_attempts
        )
        
        # Queue for delivery
        send_webhook_notification(webhook_log.webhook_id)
        webhook_count += 1
    
    logger.info(f'Triggered {webhook_count} webhooks for event {event_type}')
    return webhook_count