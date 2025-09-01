from django.db import models
from django.utils import timezone
import hashlib
import hmac
import json
from datetime import datetime, timedelta

class WebhookConfig(models.Model):
    config_id = models.AutoField(primary_key=True)
    client_id = models.CharField(max_length=50)
    endpoint_url = models.URLField(max_length=500)
    secret_key = models.CharField(max_length=255)
    events_subscribed = models.JSONField(default=list)  # ["payment.success", "refund.processed"]
    is_active = models.BooleanField(default=True)
    max_retry_attempts = models.IntegerField(default=3)
    retry_delay_minutes = models.IntegerField(default=5)  # 5, 15, 60 minute intervals
    timeout_seconds = models.IntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=100)

    class Meta:
        db_table = 'webhook_config'
        managed = True  # We'll create this table

    def generate_signature(self, payload):
        """Generate HMAC-SHA256 signature for webhook payload"""
        message = json.dumps(payload, sort_keys=True).encode('utf-8')
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            message,
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"

class WebhookLogs(models.Model):
    webhook_id = models.AutoField(primary_key=True)
    client_id = models.CharField(max_length=50)
    config_id = models.IntegerField()
    event_type = models.CharField(max_length=100)  # "payment.success", "refund.processed"
    payload = models.JSONField()
    endpoint_url = models.URLField(max_length=500)
    delivery_status = models.CharField(max_length=20, default='PENDING')  # PENDING, SUCCESS, FAILED, RETRY
    http_status_code = models.IntegerField(null=True)
    response_body = models.TextField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    next_retry_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True)
    signature_sent = models.CharField(max_length=255, null=True)

    class Meta:
        db_table = 'webhook_logs'
        managed = True  # We'll create this table

    @property
    def is_delivery_successful(self):
        return self.delivery_status == 'SUCCESS' and self.http_status_code in [200, 201, 202]

    @property
    def can_retry(self):
        return (
            self.delivery_status in ['PENDING', 'FAILED', 'RETRY'] and
            self.attempts < self.max_attempts and
            self.next_retry_at and
            timezone.now() >= self.next_retry_at
        )

class GatewayWebhookLogs(models.Model):
    """Reference to existing gateway webhook logs table"""
    log_id = models.AutoField(primary_key=True)
    gateway_code = models.CharField(max_length=50)
    webhook_type = models.CharField(max_length=50)
    txn_id = models.CharField(max_length=100, null=True)
    pg_txn_id = models.CharField(max_length=100, null=True)
    request_headers = models.JSONField()
    request_body = models.JSONField()
    response_status = models.IntegerField()
    response_body = models.JSONField(null=True)
    signature_valid = models.BooleanField()
    processed = models.BooleanField()
    processing_time_ms = models.IntegerField(null=True)
    ip_address = models.GenericIPAddressField()
    created_at = models.DateTimeField()

    class Meta:
        db_table = 'gateway_webhook_logs'
        managed = False  # This table already exists

class WebhookEventQueue(models.Model):
    """Queue for webhook events to be processed"""
    queue_id = models.AutoField(primary_key=True)
    client_id = models.CharField(max_length=50)
    event_type = models.CharField(max_length=100)
    event_data = models.JSONField()
    status = models.CharField(max_length=20, default='QUEUED')  # QUEUED, PROCESSING, COMPLETED, FAILED
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True)
    error_message = models.TextField(null=True)
    
    class Meta:
        db_table = 'webhook_event_queue'
        managed = True

class WebhookTemplate(models.Model):
    """Templates for webhook payloads"""
    template_id = models.AutoField(primary_key=True)
    event_type = models.CharField(max_length=100, unique=True)
    payload_template = models.JSONField()
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'webhook_templates'
        managed = True
