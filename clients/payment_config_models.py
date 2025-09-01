"""
Client Payment Configuration Models
Manages payment methods and configurations per client
"""
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.utils import timezone
import uuid


class PaymentConfiguration(models.Model):
    """
    Payment configuration for each client
    """
    config_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey('ClientDataTable', on_delete=models.CASCADE, related_name='payment_configs')
    
    # Payment method configurations
    payment_methods = JSONField(default=dict)  # {method_name: {enabled: bool, config: {}}}
    
    # Card payment settings
    card_enabled = models.BooleanField(default=True)
    card_min_amount = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)
    card_max_amount = models.DecimalField(max_digits=10, decimal_places=2, default=100000.00)
    card_processing_fee = models.DecimalField(max_digits=5, decimal_places=2, default=2.00)  # Percentage
    
    # Net banking settings
    netbanking_enabled = models.BooleanField(default=True)
    netbanking_banks = JSONField(default=list)  # List of enabled bank codes
    netbanking_processing_fee = models.DecimalField(max_digits=5, decimal_places=2, default=1.50)
    
    # UPI settings
    upi_enabled = models.BooleanField(default=True)
    upi_vpa = models.CharField(max_length=255, blank=True)
    upi_processing_fee = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    
    # Wallet settings
    wallet_enabled = models.BooleanField(default=False)
    wallet_providers = JSONField(default=list)  # List of enabled wallet providers
    wallet_processing_fee = models.DecimalField(max_digits=5, decimal_places=2, default=1.50)
    
    # Gateway configuration
    gateway_merchant_id = models.CharField(max_length=255, blank=True)
    gateway_api_key = models.CharField(max_length=500, blank=True)  # Encrypted
    gateway_secret_key = models.CharField(max_length=500, blank=True)  # Encrypted
    gateway_webhook_secret = models.CharField(max_length=500, blank=True)  # Encrypted
    
    # Transaction limits
    daily_transaction_limit = models.DecimalField(max_digits=12, decimal_places=2, default=10000000.00)
    monthly_transaction_limit = models.DecimalField(max_digits=12, decimal_places=2, default=300000000.00)
    max_transaction_amount = models.DecimalField(max_digits=10, decimal_places=2, default=500000.00)
    min_transaction_amount = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)
    
    # Settlement configuration
    settlement_cycle = models.CharField(max_length=20, choices=[
        ('T+0', 'Same Day'),
        ('T+1', 'Next Day'),
        ('T+2', 'Two Days'),
        ('T+3', 'Three Days'),
        ('WEEKLY', 'Weekly'),
    ], default='T+1')
    settlement_account_number = models.CharField(max_length=50, blank=True)
    settlement_ifsc_code = models.CharField(max_length=15, blank=True)
    settlement_account_name = models.CharField(max_length=255, blank=True)
    
    # Risk management
    fraud_check_enabled = models.BooleanField(default=True)
    risk_score_threshold = models.IntegerField(default=70)  # 0-100
    auto_refund_enabled = models.BooleanField(default=False)
    duplicate_check_window = models.IntegerField(default=300)  # seconds
    
    # Status and metadata
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey('authentication.AdminUser', on_delete=models.SET_NULL, 
                                   null=True, blank=True, related_name='verified_configs')
    
    # Sync status with gateway
    last_synced_at = models.DateTimeField(null=True, blank=True)
    sync_status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ], default='PENDING')
    sync_error = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('authentication.AdminUser', on_delete=models.SET_NULL, 
                                  null=True, related_name='created_payment_configs')
    updated_by = models.ForeignKey('authentication.AdminUser', on_delete=models.SET_NULL, 
                                  null=True, related_name='updated_payment_configs')
    
    class Meta:
        db_table = 'client_payment_configurations'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['client', 'is_active']),
            models.Index(fields=['sync_status']),
        ]
    
    def __str__(self):
        return f"Payment Config for {self.client.client_name}"
    
    def sync_with_gateway(self):
        """Sync configuration with payment gateway"""
        # Implementation for gateway sync
        pass


class PaymentMethod(models.Model):
    """
    Available payment methods in the system
    """
    method_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    method_code = models.CharField(max_length=50, unique=True)
    method_name = models.CharField(max_length=100)
    method_type = models.CharField(max_length=50, choices=[
        ('CARD', 'Card Payment'),
        ('NETBANKING', 'Net Banking'),
        ('UPI', 'UPI'),
        ('WALLET', 'Digital Wallet'),
        ('EMI', 'EMI'),
        ('BNPL', 'Buy Now Pay Later'),
    ])
    
    # Provider information
    provider_name = models.CharField(max_length=100)
    provider_code = models.CharField(max_length=50)
    
    # Configuration
    is_active = models.BooleanField(default=True)
    requires_otp = models.BooleanField(default=False)
    requires_3ds = models.BooleanField(default=False)
    
    # Limits
    min_amount = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)
    max_amount = models.DecimalField(max_digits=10, decimal_places=2, default=100000.00)
    
    # Processing
    processing_time = models.IntegerField(default=300)  # seconds
    success_rate = models.DecimalField(max_digits=5, decimal_places=2, default=95.00)  # percentage
    
    # Metadata
    icon_url = models.URLField(blank=True)
    description = models.TextField(blank=True)
    terms_conditions = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payment_methods'
        ordering = ['method_type', 'method_name']
    
    def __str__(self):
        return f"{self.method_name} ({self.method_type})"


class ClientPaymentMethod(models.Model):
    """
    Payment methods enabled for specific clients
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey('ClientDataTable', on_delete=models.CASCADE, related_name='client_payment_methods')
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE)
    config = models.ForeignKey(PaymentConfiguration, on_delete=models.CASCADE)
    
    # Custom settings for this client-method combination
    is_enabled = models.BooleanField(default=True)
    custom_fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    custom_min_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    custom_max_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Priority for display
    display_priority = models.IntegerField(default=100)
    
    # Custom branding
    custom_display_name = models.CharField(max_length=100, blank=True)
    custom_description = models.TextField(blank=True)
    
    # Usage statistics
    total_transactions = models.IntegerField(default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    success_count = models.IntegerField(default=0)
    failure_count = models.IntegerField(default=0)
    last_used_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'client_payment_methods'
        unique_together = ['client', 'payment_method']
        ordering = ['display_priority', 'payment_method__method_name']
    
    def __str__(self):
        return f"{self.client.client_name} - {self.payment_method.method_name}"
    
    @property
    def success_rate(self):
        """Calculate success rate"""
        total = self.success_count + self.failure_count
        if total == 0:
            return 0
        return (self.success_count / total) * 100


class PaymentConfigurationHistory(models.Model):
    """
    Track changes to payment configurations
    """
    history_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    config = models.ForeignKey(PaymentConfiguration, on_delete=models.CASCADE, 
                             related_name='configuration_history')
    
    # Change information
    change_type = models.CharField(max_length=20, choices=[
        ('CREATE', 'Created'),
        ('UPDATE', 'Updated'),
        ('ENABLE', 'Enabled'),
        ('DISABLE', 'Disabled'),
        ('VERIFY', 'Verified'),
        ('SYNC', 'Synced'),
    ])
    
    # What changed
    field_name = models.CharField(max_length=100, blank=True)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    change_reason = models.TextField(blank=True)
    
    # Who made the change
    changed_by = models.ForeignKey('authentication.AdminUser', on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Approval if required
    requires_approval = models.BooleanField(default=False)
    approved_by = models.ForeignKey('authentication.AdminUser', on_delete=models.SET_NULL, 
                                   null=True, blank=True, related_name='approved_config_changes')
    approved_at = models.DateTimeField(null=True, blank=True)
    approval_status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ], default='PENDING')
    
    class Meta:
        db_table = 'payment_configuration_history'
        ordering = ['-changed_at']
    
    def __str__(self):
        return f"{self.change_type} - {self.config.client.client_name} at {self.changed_at}"