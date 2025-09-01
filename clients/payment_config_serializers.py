"""
Payment Configuration Serializers
"""
from rest_framework import serializers
from .payment_config_models import (
    PaymentConfiguration, PaymentMethod, ClientPaymentMethod,
    PaymentConfigurationHistory
)


class PaymentConfigurationSerializer(serializers.ModelSerializer):
    """
    Serializer for PaymentConfiguration
    """
    client_name = serializers.CharField(source='client.client_name', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.username', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = PaymentConfiguration
        fields = [
            'config_id', 'client', 'client_name', 'payment_methods',
            'card_enabled', 'card_min_amount', 'card_max_amount', 'card_processing_fee',
            'netbanking_enabled', 'netbanking_banks', 'netbanking_processing_fee',
            'upi_enabled', 'upi_vpa', 'upi_processing_fee',
            'wallet_enabled', 'wallet_providers', 'wallet_processing_fee',
            'gateway_merchant_id', 'daily_transaction_limit', 'monthly_transaction_limit',
            'max_transaction_amount', 'min_transaction_amount',
            'settlement_cycle', 'settlement_account_number', 'settlement_ifsc_code',
            'settlement_account_name', 'fraud_check_enabled', 'risk_score_threshold',
            'auto_refund_enabled', 'duplicate_check_window',
            'is_active', 'is_verified', 'verified_at', 'verified_by_name',
            'last_synced_at', 'sync_status', 'sync_error',
            'created_at', 'updated_at', 'created_by_name'
        ]
        read_only_fields = [
            'config_id', 'verified_at', 'verified_by_name', 'last_synced_at',
            'sync_status', 'sync_error', 'created_at', 'updated_at', 'created_by_name'
        ]


class PaymentConfigurationCreateSerializer(serializers.Serializer):
    """
    Serializer for creating PaymentConfiguration
    """
    client_id = serializers.UUIDField()
    
    # Card settings
    card_enabled = serializers.BooleanField(default=True)
    card_min_amount = serializers.DecimalField(max_digits=10, decimal_places=2, default=1.00)
    card_max_amount = serializers.DecimalField(max_digits=10, decimal_places=2, default=100000.00)
    card_processing_fee = serializers.DecimalField(max_digits=5, decimal_places=2, default=2.00)
    
    # Net banking settings
    netbanking_enabled = serializers.BooleanField(default=True)
    netbanking_banks = serializers.ListField(default=list)
    netbanking_processing_fee = serializers.DecimalField(max_digits=5, decimal_places=2, default=1.50)
    
    # UPI settings
    upi_enabled = serializers.BooleanField(default=True)
    upi_vpa = serializers.CharField(max_length=255, required=False, allow_blank=True)
    upi_processing_fee = serializers.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    
    # Wallet settings
    wallet_enabled = serializers.BooleanField(default=False)
    wallet_providers = serializers.ListField(default=list)
    wallet_processing_fee = serializers.DecimalField(max_digits=5, decimal_places=2, default=1.50)
    
    # Gateway configuration
    gateway_merchant_id = serializers.CharField(max_length=255, required=False, allow_blank=True)
    gateway_api_key = serializers.CharField(max_length=500, required=False, allow_blank=True)
    gateway_secret_key = serializers.CharField(max_length=500, required=False, allow_blank=True)
    gateway_webhook_secret = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    # Transaction limits
    daily_transaction_limit = serializers.DecimalField(max_digits=12, decimal_places=2, default=10000000.00)
    monthly_transaction_limit = serializers.DecimalField(max_digits=12, decimal_places=2, default=300000000.00)
    max_transaction_amount = serializers.DecimalField(max_digits=10, decimal_places=2, default=500000.00)
    min_transaction_amount = serializers.DecimalField(max_digits=10, decimal_places=2, default=1.00)
    
    # Settlement configuration
    settlement_cycle = serializers.ChoiceField(choices=['T+0', 'T+1', 'T+2', 'T+3', 'WEEKLY'], default='T+1')
    settlement_account_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    settlement_ifsc_code = serializers.CharField(max_length=15, required=False, allow_blank=True)
    settlement_account_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    
    # Risk management
    fraud_check_enabled = serializers.BooleanField(default=True)
    risk_score_threshold = serializers.IntegerField(default=70)
    auto_refund_enabled = serializers.BooleanField(default=False)
    duplicate_check_window = serializers.IntegerField(default=300)


class PaymentConfigurationUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating PaymentConfiguration
    """
    # Card settings
    card_enabled = serializers.BooleanField(required=False)
    card_min_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    card_max_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    card_processing_fee = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    
    # Net banking settings  
    netbanking_enabled = serializers.BooleanField(required=False)
    netbanking_banks = serializers.ListField(required=False)
    netbanking_processing_fee = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    
    # UPI settings
    upi_enabled = serializers.BooleanField(required=False)
    upi_vpa = serializers.CharField(max_length=255, required=False, allow_blank=True)
    upi_processing_fee = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    
    # Wallet settings
    wallet_enabled = serializers.BooleanField(required=False)
    wallet_providers = serializers.ListField(required=False)
    wallet_processing_fee = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    
    # Gateway configuration
    gateway_merchant_id = serializers.CharField(max_length=255, required=False, allow_blank=True)
    gateway_api_key = serializers.CharField(max_length=500, required=False, allow_blank=True)
    gateway_secret_key = serializers.CharField(max_length=500, required=False, allow_blank=True)
    gateway_webhook_secret = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    # Transaction limits
    daily_transaction_limit = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    monthly_transaction_limit = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    max_transaction_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    min_transaction_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    
    # Settlement configuration
    settlement_cycle = serializers.ChoiceField(choices=['T+0', 'T+1', 'T+2', 'T+3', 'WEEKLY'], required=False)
    settlement_account_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    settlement_ifsc_code = serializers.CharField(max_length=15, required=False, allow_blank=True)
    settlement_account_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    
    # Risk management
    fraud_check_enabled = serializers.BooleanField(required=False)
    risk_score_threshold = serializers.IntegerField(required=False)
    auto_refund_enabled = serializers.BooleanField(required=False)
    duplicate_check_window = serializers.IntegerField(required=False)


class PaymentMethodSerializer(serializers.ModelSerializer):
    """
    Serializer for PaymentMethod
    """
    class Meta:
        model = PaymentMethod
        fields = [
            'method_id', 'method_code', 'method_name', 'method_type',
            'provider_name', 'provider_code', 'is_active',
            'requires_otp', 'requires_3ds', 'min_amount', 'max_amount',
            'processing_time', 'success_rate', 'icon_url',
            'description', 'terms_conditions', 'created_at', 'updated_at'
        ]
        read_only_fields = ['method_id', 'created_at', 'updated_at']


class ClientPaymentMethodSerializer(serializers.ModelSerializer):
    """
    Serializer for ClientPaymentMethod
    """
    method_name = serializers.CharField(source='payment_method.method_name', read_only=True)
    method_type = serializers.CharField(source='payment_method.method_type', read_only=True)
    method_code = serializers.CharField(source='payment_method.method_code', read_only=True)
    client_name = serializers.CharField(source='client.client_name', read_only=True)
    success_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = ClientPaymentMethod
        fields = [
            'id', 'client', 'client_name', 'payment_method',
            'method_name', 'method_type', 'method_code',
            'is_enabled', 'custom_fee_percentage', 'custom_min_amount',
            'custom_max_amount', 'display_priority', 'custom_display_name',
            'custom_description', 'total_transactions', 'total_amount',
            'success_count', 'failure_count', 'success_rate',
            'last_used_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'total_transactions', 'total_amount', 'success_count',
            'failure_count', 'last_used_at', 'created_at', 'updated_at'
        ]
    
    def get_success_rate(self, obj):
        return obj.success_rate


class PaymentConfigurationHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for PaymentConfigurationHistory
    """
    changed_by_name = serializers.CharField(source='changed_by.username', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True)
    config_client = serializers.CharField(source='config.client.client_name', read_only=True)
    
    class Meta:
        model = PaymentConfigurationHistory
        fields = [
            'history_id', 'config', 'config_client', 'change_type',
            'field_name', 'old_value', 'new_value', 'change_reason',
            'changed_by', 'changed_by_name', 'changed_at', 'ip_address',
            'requires_approval', 'approved_by', 'approved_by_name',
            'approved_at', 'approval_status'
        ]
        read_only_fields = ['history_id', 'changed_at']