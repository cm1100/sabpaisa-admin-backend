from rest_framework import serializers
from .models import GatewaySyncQueue, GatewayConfiguration, GatewaySyncLog, GatewayWebhookLog, TransactionDetail


class GatewaySyncQueueSerializer(serializers.ModelSerializer):
    """Serializer for gateway sync queue"""
    
    class Meta:
        model = GatewaySyncQueue
        fields = [
            'sync_id', 'txn_id', 'pg_txn_id', 'sync_type', 'priority',
            'status', 'attempts', 'max_attempts', 'next_retry_at',
            'request_data', 'response_data', 'error_message',
            'created_at', 'updated_at', 'processed_at'
        ]
        read_only_fields = ['sync_id', 'created_at', 'updated_at', 'processed_at']
    
    def validate_priority(self, value):
        """Validate priority is within acceptable range"""
        if value not in [1, 2, 3]:
            raise serializers.ValidationError("Priority must be 1 (High), 2 (Medium), or 3 (Low)")
        return value
    
    def validate_sync_type(self, value):
        """Validate sync type"""
        valid_types = ['STATUS_CHECK', 'REFUND_STATUS', 'SETTLEMENT_STATUS']
        if value not in valid_types:
            raise serializers.ValidationError(f"Sync type must be one of: {', '.join(valid_types)}")
        return value


class GatewayConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for gateway configuration"""
    
    class Meta:
        model = GatewayConfiguration
        fields = [
            'gateway_id', 'gateway_name', 'gateway_code', 'api_endpoint',
            'status_check_endpoint', 'refund_endpoint', 'api_key', 'api_secret',
            'webhook_secret', 'timeout_seconds', 'max_retry_attempts',
            'retry_delay_seconds', 'is_active', 'supports_webhook',
            'webhook_url', 'created_at', 'updated_at'
        ]
        read_only_fields = ['gateway_id', 'created_at', 'updated_at']
        extra_kwargs = {
            'api_secret': {'write_only': True},
            'webhook_secret': {'write_only': True}
        }
    
    def validate_timeout_seconds(self, value):
        """Validate timeout is reasonable"""
        if value < 5 or value > 120:
            raise serializers.ValidationError("Timeout must be between 5 and 120 seconds")
        return value
    
    def validate_max_retry_attempts(self, value):
        """Validate retry attempts"""
        if value < 0 or value > 10:
            raise serializers.ValidationError("Max retry attempts must be between 0 and 10")
        return value


class GatewaySyncLogSerializer(serializers.ModelSerializer):
    """Serializer for gateway sync logs"""
    
    class Meta:
        model = GatewaySyncLog
        fields = [
            'log_id', 'sync_queue_id', 'operation', 'request_url',
            'request_method', 'request_headers', 'request_body',
            'response_status', 'response_headers', 'response_body',
            'response_time_ms', 'success', 'error_message', 'created_at'
        ]
        read_only_fields = ['log_id', 'created_at']


class GatewayWebhookLogSerializer(serializers.ModelSerializer):
    """Serializer for gateway webhook logs"""
    
    class Meta:
        model = GatewayWebhookLog
        fields = [
            'log_id', 'gateway_code', 'webhook_type', 'txn_id', 'pg_txn_id',
            'request_headers', 'request_body', 'response_status', 'response_body',
            'signature_valid', 'processed', 'processing_time_ms',
            'ip_address', 'created_at'
        ]
        read_only_fields = ['log_id', 'created_at']


class TransactionDetailSerializer(serializers.ModelSerializer):
    """Serializer for transaction details (read-only reference)"""
    
    class Meta:
        model = TransactionDetail
        fields = [
            'txn_id', 'pg_txn_id', 'status', 'pg_name', 'pg_response_code',
            'resp_msg', 'refund_status_code', 'refunded_date', 'refunded_amount',
            'is_refunded', 'refund_message', 'is_settled', 'settlement_date',
            'settlement_status', 'created_date', 'updated_date'
        ]
        read_only_fields = ['created_date', 'updated_date']


class SyncOperationRequestSerializer(serializers.Serializer):
    """Serializer for sync operation requests"""
    force = serializers.BooleanField(default=False)
    priority = serializers.IntegerField(default=2, min_value=1, max_value=3)
    pg_txn_id = serializers.CharField(max_length=100, required=False, allow_blank=True)


class SyncStatsSerializer(serializers.Serializer):
    """Serializer for sync statistics response"""
    total_items = serializers.IntegerField()
    pending_items = serializers.IntegerField()
    processing_items = serializers.IntegerField()
    completed_items = serializers.IntegerField()
    failed_items = serializers.IntegerField()
    avg_attempts = serializers.FloatField()
    recent_total = serializers.IntegerField()
    recent_completed = serializers.IntegerField()
    recent_failed = serializers.IntegerField()


class SyncDashboardSerializer(serializers.Serializer):
    """Serializer for sync dashboard response"""
    recent_activity = serializers.DictField()
    queue_status = serializers.DictField()
    performance = serializers.DictField()
    gateway_stats = serializers.ListField()
    recent_errors = serializers.ListField()
    webhook_stats = serializers.DictField()
    timestamp = serializers.DateTimeField()
    system_health = serializers.CharField()