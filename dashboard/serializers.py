"""
Dashboard Serializers - Following SOLID Principles
Interface Segregation: Specific serializers for different metric types
"""
from rest_framework import serializers


class TransactionMetricsSerializer(serializers.Serializer):
    """Single Responsibility: Only transaction metrics serialization"""
    total_transactions = serializers.IntegerField()
    today_transactions = serializers.IntegerField()
    yesterday_transactions = serializers.IntegerField()
    weekly_transactions = serializers.IntegerField()
    monthly_transactions = serializers.IntegerField()
    success_rate = serializers.FloatField()
    failed_transactions = serializers.IntegerField()
    pending_transactions = serializers.IntegerField()
    average_transaction_value = serializers.FloatField()
    peak_hour = serializers.IntegerField()
    transaction_growth = serializers.FloatField()


class RevenueMetricsSerializer(serializers.Serializer):
    """Single Responsibility: Only revenue metrics serialization"""
    total_revenue = serializers.FloatField()
    today_revenue = serializers.FloatField()
    yesterday_revenue = serializers.FloatField()
    weekly_revenue = serializers.FloatField()
    monthly_revenue = serializers.FloatField()
    average_fee = serializers.FloatField()
    total_fees_collected = serializers.FloatField()
    revenue_growth = serializers.FloatField()
    highest_revenue_day = serializers.CharField()
    projected_monthly = serializers.FloatField()


class ClientMetricsSerializer(serializers.Serializer):
    """Single Responsibility: Only client metrics serialization"""
    total_clients = serializers.IntegerField()
    active_clients = serializers.IntegerField()
    inactive_clients = serializers.IntegerField()
    new_clients_today = serializers.IntegerField()
    new_clients_week = serializers.IntegerField()
    new_clients_month = serializers.IntegerField()
    enterprise_clients = serializers.IntegerField()
    premium_clients = serializers.IntegerField()
    standard_clients = serializers.IntegerField()
    basic_clients = serializers.IntegerField()
    client_growth = serializers.FloatField()


class SettlementMetricsSerializer(serializers.Serializer):
    """Single Responsibility: Only settlement metrics serialization"""
    pending_settlements = serializers.IntegerField()
    completed_settlements = serializers.IntegerField()
    total_settlement_amount = serializers.FloatField()
    today_settlements = serializers.IntegerField()
    settlement_success_rate = serializers.FloatField()
    average_settlement_time = serializers.FloatField()
    failed_settlements = serializers.IntegerField()
    settlements_in_progress = serializers.IntegerField()


class SystemHealthSerializer(serializers.Serializer):
    """Single Responsibility: Only system health serialization"""
    api_status = serializers.CharField()
    database_status = serializers.CharField()
    redis_status = serializers.CharField()
    gateway_sync_status = serializers.CharField()
    uptime_percentage = serializers.FloatField()
    response_time_avg = serializers.IntegerField()
    error_rate = serializers.FloatField()
    cpu_usage = serializers.FloatField()
    memory_usage = serializers.FloatField()
    disk_usage = serializers.FloatField()


class HourlyVolumeSerializer(serializers.Serializer):
    """Single Responsibility: Only hourly volume serialization"""
    hour = serializers.CharField()
    volume = serializers.IntegerField()
    amount = serializers.FloatField()
    success_rate = serializers.FloatField()


class PaymentModeSerializer(serializers.Serializer):
    """Single Responsibility: Only payment mode serialization"""
    mode = serializers.CharField()
    count = serializers.IntegerField()
    percentage = serializers.FloatField()


class RecentTransactionSerializer(serializers.Serializer):
    """Single Responsibility: Only recent transaction serialization"""
    id = serializers.CharField()
    client = serializers.CharField()
    amount = serializers.FloatField()
    payment_mode = serializers.CharField()
    status = serializers.CharField()
    timestamp = serializers.DateTimeField()


class TopClientSerializer(serializers.Serializer):
    """Single Responsibility: Only top client serialization"""
    name = serializers.CharField()
    transactions = serializers.IntegerField()
    revenue = serializers.FloatField()
    volume = serializers.FloatField()
    growth = serializers.FloatField()


class DashboardDataSerializer(serializers.Serializer):
    """
    Main dashboard serializer
    Open/Closed: Can add new metric types without modifying existing
    """
    transactions = TransactionMetricsSerializer()
    revenue = RevenueMetricsSerializer()
    clients = ClientMetricsSerializer()
    settlements = SettlementMetricsSerializer()
    system_health = SystemHealthSerializer()
    hourly_volume = HourlyVolumeSerializer(many=True)
    payment_modes = PaymentModeSerializer(many=True)
    recent_transactions = RecentTransactionSerializer(many=True)
    top_clients = TopClientSerializer(many=True)
    timestamp = serializers.DateTimeField()


# Add missing serializer aliases for compatibility
DashboardMetricsSerializer = DashboardDataSerializer
PaymentModeDistributionSerializer = PaymentModeSerializer
TopClientsSerializer = TopClientSerializer
ClientStatsSerializer = ClientMetricsSerializer