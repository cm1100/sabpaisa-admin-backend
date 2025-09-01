from django.db import models
from django.utils import timezone
import uuid


class GatewaySyncQueue(models.Model):
    """Queue for gateway synchronization tasks"""
    sync_id = models.AutoField(primary_key=True)
    txn_id = models.CharField(max_length=100)
    pg_txn_id = models.CharField(max_length=100, null=True, blank=True)
    sync_type = models.CharField(max_length=50)  # STATUS_CHECK, REFUND_STATUS, SETTLEMENT_STATUS
    priority = models.IntegerField(default=1)  # 1=High, 2=Medium, 3=Low
    status = models.CharField(max_length=20, default='PENDING')  # PENDING, PROCESSING, COMPLETED, FAILED
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    request_data = models.JSONField(null=True, blank=True)
    response_data = models.JSONField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'gateway_sync_queue'
        indexes = [
            models.Index(fields=['status', 'priority', 'next_retry_at']),
            models.Index(fields=['txn_id']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Sync {self.sync_id}: {self.txn_id} - {self.sync_type} ({self.status})"


class GatewayConfiguration(models.Model):
    """Gateway configuration for different payment gateways"""
    gateway_id = models.AutoField(primary_key=True)
    gateway_name = models.CharField(max_length=100, unique=True)
    gateway_code = models.CharField(max_length=50, unique=True)
    api_endpoint = models.URLField()
    status_check_endpoint = models.URLField()
    refund_endpoint = models.URLField(null=True, blank=True)
    api_key = models.CharField(max_length=255)
    api_secret = models.CharField(max_length=255)
    webhook_secret = models.CharField(max_length=255, null=True, blank=True)
    timeout_seconds = models.IntegerField(default=30)
    max_retry_attempts = models.IntegerField(default=3)
    retry_delay_seconds = models.IntegerField(default=10)
    is_active = models.BooleanField(default=True)
    supports_webhook = models.BooleanField(default=True)
    webhook_url = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'gateway_configurations'

    def __str__(self):
        return f"{self.gateway_name} ({self.gateway_code})"


class GatewayWebhookLog(models.Model):
    """Log all webhook calls from payment gateways"""
    log_id = models.AutoField(primary_key=True)
    gateway_code = models.CharField(max_length=50)
    webhook_type = models.CharField(max_length=50)  # PAYMENT_STATUS, REFUND_STATUS, SETTLEMENT
    txn_id = models.CharField(max_length=100, null=True, blank=True)
    pg_txn_id = models.CharField(max_length=100, null=True, blank=True)
    request_headers = models.JSONField()
    request_body = models.JSONField()
    response_status = models.IntegerField()
    response_body = models.JSONField(null=True, blank=True)
    signature_valid = models.BooleanField(default=False)
    processed = models.BooleanField(default=False)
    processing_time_ms = models.IntegerField(null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'gateway_webhook_logs'
        indexes = [
            models.Index(fields=['txn_id']),
            models.Index(fields=['created_at']),
            models.Index(fields=['gateway_code']),
        ]

    def __str__(self):
        return f"Webhook {self.log_id}: {self.gateway_code} - {self.webhook_type}"


class GatewaySyncLog(models.Model):
    """Detailed sync operation logs"""
    log_id = models.AutoField(primary_key=True)
    sync_queue_id = models.IntegerField()
    operation = models.CharField(max_length=50)  # STATUS_CHECK, UPDATE, RETRY
    request_url = models.URLField()
    request_method = models.CharField(max_length=10)
    request_headers = models.JSONField()
    request_body = models.JSONField(null=True, blank=True)
    response_status = models.IntegerField(null=True, blank=True)
    response_headers = models.JSONField(null=True, blank=True)
    response_body = models.JSONField(null=True, blank=True)
    response_time_ms = models.IntegerField(null=True, blank=True)
    success = models.BooleanField(default=False)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'gateway_sync_logs'
        indexes = [
            models.Index(fields=['sync_queue_id']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Log {self.log_id}: {self.operation} - {'Success' if self.success else 'Failed'}"


# Reference to existing TransactionDetail model for status updates
class TransactionDetail(models.Model):
    """Reference to main transaction table for status updates"""
    txn_id = models.CharField(max_length=100, primary_key=True)
    pg_txn_id = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=50)
    pg_name = models.CharField(max_length=50, null=True, blank=True)  # Gateway name
    pg_response_code = models.CharField(max_length=50, null=True, blank=True)
    resp_msg = models.TextField(null=True, blank=True)
    refund_status_code = models.CharField(max_length=50, null=True, blank=True)
    refunded_date = models.DateTimeField(null=True, blank=True)
    refunded_amount = models.FloatField(null=True, blank=True)
    is_refunded = models.BooleanField(default=False)
    refund_message = models.TextField(null=True, blank=True)
    is_settled = models.BooleanField(default=False)
    settlement_date = models.DateTimeField(null=True, blank=True)
    settlement_status = models.CharField(max_length=50, null=True, blank=True)
    created_date = models.DateTimeField(null=True, blank=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'transaction_detail'
        managed = False  # This table is managed elsewhere

    def __str__(self):
        return f"Transaction {self.txn_id}: {self.status}"
