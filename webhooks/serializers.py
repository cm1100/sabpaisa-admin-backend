from rest_framework import serializers
from .models import WebhookConfig, WebhookLogs, WebhookEventQueue, WebhookTemplate
from datetime import datetime

class WebhookConfigSerializer(serializers.ModelSerializer):
    events_available = serializers.SerializerMethodField()
    total_deliveries = serializers.SerializerMethodField()
    success_rate = serializers.SerializerMethodField()

    class Meta:
        model = WebhookConfig
        fields = '__all__'
        read_only_fields = ['config_id', 'created_at', 'updated_at', 'created_by']

    def get_events_available(self, obj):
        return [
            "payment.success", "payment.failed", "payment.pending",
            "refund.processed", "refund.failed", "settlement.completed",
            "transaction.disputed", "kyc.approved", "kyc.rejected"
        ]

    def get_total_deliveries(self, obj):
        return WebhookLogs.objects.filter(config_id=obj.config_id).count()

    def get_success_rate(self, obj):
        total = WebhookLogs.objects.filter(config_id=obj.config_id).count()
        if total == 0:
            return 100
        successful = WebhookLogs.objects.filter(
            config_id=obj.config_id,
            delivery_status='SUCCESS'
        ).count()
        return round((successful / total) * 100, 2)

    def validate_events_subscribed(self, value):
        available_events = self.get_events_available(None)
        invalid_events = [event for event in value if event not in available_events]
        if invalid_events:
            raise serializers.ValidationError(f"Invalid events: {invalid_events}")
        return value

    def validate_endpoint_url(self, value):
        if not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("URL must start with http:// or https://")
        return value

class WebhookLogsSerializer(serializers.ModelSerializer):
    time_since_created = serializers.SerializerMethodField()
    retry_info = serializers.SerializerMethodField()

    class Meta:
        model = WebhookLogs
        fields = '__all__'

    def get_time_since_created(self, obj):
        delta = datetime.now() - obj.created_at.replace(tzinfo=None)
        if delta.days > 0:
            return f"{delta.days} days ago"
        elif delta.seconds > 3600:
            return f"{delta.seconds // 3600} hours ago"
        elif delta.seconds > 60:
            return f"{delta.seconds // 60} minutes ago"
        else:
            return "Just now"

    def get_retry_info(self, obj):
        if obj.delivery_status in ['PENDING', 'FAILED', 'RETRY']:
            return {
                'can_retry': obj.can_retry,
                'attempts_remaining': obj.max_attempts - obj.attempts,
                'next_retry_at': obj.next_retry_at
            }
        return None

class WebhookTestSerializer(serializers.Serializer):
    event_type = serializers.CharField(max_length=100)
    test_payload = serializers.JSONField()

class BulkRetrySerializer(serializers.Serializer):
    client_id = serializers.CharField(max_length=50)
    max_age_hours = serializers.IntegerField(default=24)

class WebhookStatsSerializer(serializers.Serializer):
    total_webhooks = serializers.IntegerField()
    last_7_days = serializers.DictField()
    success_rate_7_days = serializers.FloatField()
    avg_response_time = serializers.CharField()
    most_failed_endpoints = serializers.ListField()

class WebhookEventQueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookEventQueue
        fields = '__all__'
        read_only_fields = ['queue_id', 'created_at', 'processed_at']

class WebhookTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookTemplate
        fields = '__all__'
        read_only_fields = ['template_id', 'created_at', 'updated_at']