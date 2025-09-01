from django.db import models
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP
import json
from datetime import datetime, timedelta

class FeeConfiguration(models.Model):
    FEE_TYPES = [
        ('TRANSACTION', 'Transaction Fee'),
        ('PROCESSING', 'Processing Fee'),
        ('SETTLEMENT', 'Settlement Fee'),
        ('REFUND', 'Refund Fee'),
        ('CHARGEBACK', 'Chargeback Fee'),
        ('MONTHLY', 'Monthly Fee'),
        ('ANNUAL', 'Annual Fee'),
        ('SETUP', 'Setup Fee')
    ]
    
    FEE_STRUCTURES = [
        ('FLAT', 'Flat Rate'),
        ('PERCENTAGE', 'Percentage'),
        ('TIERED', 'Tiered Pricing'),
        ('HYBRID', 'Hybrid (Percentage + Flat)'),
        ('VOLUME_BASED', 'Volume Based'),
        ('CUSTOM', 'Custom Logic')
    ]
    
    fee_id = models.AutoField(primary_key=True)
    client_id = models.CharField(max_length=50)
    fee_name = models.CharField(max_length=100)
    fee_type = models.CharField(max_length=20, choices=FEE_TYPES)
    fee_structure = models.CharField(max_length=20, choices=FEE_STRUCTURES)
    
    # Basic fee configuration
    base_rate = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    minimum_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    maximum_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Tiered pricing configuration
    tier_rates = models.JSONField(default=list)
    volume_slabs = models.JSONField(default=list)
    
    # Payment method specific rates
    payment_method_rates = models.JSONField(default=dict)
    
    # Conditional configurations
    conditions = models.JSONField(default=dict)
    
    # Validity period
    effective_from = models.DateTimeField()
    effective_until = models.DateTimeField(null=True, blank=True)
    
    # Status and metadata
    is_active = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=False)
    approval_status = models.CharField(max_length=20, default='APPROVED')
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=100)
    approved_by = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        managed = True  # We'll create this table
        db_table = 'fee_configuration'
        unique_together = ['client_id', 'fee_type', 'effective_from']

    def __str__(self):
        return f"{self.client_id} - {self.fee_name} ({self.fee_type})"

    @property
    def is_currently_active(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.effective_from > now:
            return False
        if self.effective_until and self.effective_until < now:
            return False
        return True

    def calculate_fee(self, transaction_amount, payment_method=None, volume_data=None, **kwargs):
        """Calculate fee based on configuration and transaction details"""
        if not self.is_currently_active:
            raise ValueError("Fee configuration is not currently active")
        
        # Apply payment method specific rate if available
        rate = self.base_rate
        if payment_method and payment_method in self.payment_method_rates:
            rate = Decimal(str(self.payment_method_rates[payment_method]))
        
        # Calculate based on fee structure
        if self.fee_structure == 'FLAT':
            calculated_fee = rate
            
        elif self.fee_structure == 'PERCENTAGE':
            calculated_fee = (Decimal(str(transaction_amount)) * rate / 100)
            
        elif self.fee_structure == 'TIERED':
            calculated_fee = self._calculate_tiered_fee(transaction_amount)
            
        elif self.fee_structure == 'HYBRID':
            percentage_fee = (Decimal(str(transaction_amount)) * rate / 100)
            flat_fee = Decimal(str(self.conditions.get('flat_component', 0)))
            calculated_fee = percentage_fee + flat_fee
            
        elif self.fee_structure == 'VOLUME_BASED':
            calculated_fee = self._calculate_volume_based_fee(transaction_amount, volume_data)
            
        else:  # CUSTOM
            calculated_fee = self._calculate_custom_fee(transaction_amount, **kwargs)
        
        # Apply min/max limits
        if self.minimum_fee and calculated_fee < self.minimum_fee:
            calculated_fee = self.minimum_fee
        if self.maximum_fee and calculated_fee > self.maximum_fee:
            calculated_fee = self.maximum_fee
        
        return calculated_fee.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def _calculate_tiered_fee(self, amount):
        """Calculate fee based on tiered pricing"""
        total_fee = Decimal('0')
        remaining_amount = Decimal(str(amount))
        
        for tier in sorted(self.tier_rates, key=lambda x: x['min']):
            tier_min = Decimal(str(tier['min']))
            tier_max = Decimal(str(tier.get('max', float('inf'))))
            tier_rate = Decimal(str(tier['rate']))
            
            if remaining_amount <= 0:
                break
                
            if tier_min <= amount <= tier_max:
                # Amount falls in this tier
                applicable_amount = min(remaining_amount, tier_max - tier_min)
                total_fee += (applicable_amount * tier_rate / 100)
                remaining_amount -= applicable_amount
        
        return total_fee

    def _calculate_volume_based_fee(self, amount, volume_data):
        """Calculate fee based on volume slabs"""
        if not volume_data:
            return self.base_rate
        
        monthly_volume = Decimal(str(volume_data.get('monthly_volume', 0)))
        
        for slab in sorted(self.volume_slabs, key=lambda x: x['min']):
            slab_min = Decimal(str(slab['min']))
            slab_max = Decimal(str(slab.get('max', float('inf'))))
            slab_rate = Decimal(str(slab['rate']))
            
            if slab_min <= monthly_volume < slab_max:
                return (Decimal(str(amount)) * slab_rate / 100)
        
        return (Decimal(str(amount)) * self.base_rate / 100)

    def _calculate_custom_fee(self, amount, **kwargs):
        """Custom fee calculation logic"""
        # Implement custom logic based on conditions
        return Decimal(str(amount)) * self.base_rate / 100


class FeeCalculationLog(models.Model):
    CALCULATION_METHODS = [
        ('AUTO', 'Automatic'),
        ('MANUAL', 'Manual Override'),
        ('PROMO', 'Promotional'),
        ('BULK', 'Bulk Discount'),
        ('CUSTOM', 'Custom Logic')
    ]
    
    calc_id = models.AutoField(primary_key=True)
    transaction_id = models.CharField(max_length=100)
    fee_id = models.IntegerField()
    client_id = models.CharField(max_length=50)
    
    # Transaction details
    transaction_amount = models.DecimalField(max_digits=15, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    
    # Fee calculation details
    calculated_amount = models.DecimalField(max_digits=10, decimal_places=2)
    calculation_method = models.CharField(max_length=20, choices=CALCULATION_METHODS)
    calculation_details = models.JSONField(default=dict)
    
    # Promotional/discount details
    promo_code_applied = models.CharField(max_length=50, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_fee_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'fee_calculation_log'
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['client_id', 'created_at']),
        ]

    def __str__(self):
        return f"Calc {self.calc_id}: TXN {self.transaction_id} - {self.final_fee_amount}"


class PromotionalFees(models.Model):
    DISCOUNT_TYPES = [
        ('PERCENTAGE', 'Percentage Discount'),
        ('FLAT', 'Flat Discount'),
        ('WAIVER', 'Fee Waiver'),
        ('CASHBACK', 'Cashback')
    ]
    
    PROMO_STATUS = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('EXPIRED', 'Expired'),
        ('EXHAUSTED', 'Exhausted')
    ]
    
    promo_id = models.AutoField(primary_key=True)
    client_id = models.CharField(max_length=50)
    promo_code = models.CharField(max_length=50, unique=True)
    promo_name = models.CharField(max_length=100)
    description = models.TextField()
    
    # Discount configuration
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    max_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Validity
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    
    # Usage limits
    usage_limit = models.IntegerField(default=1)
    used_count = models.IntegerField(default=0)
    usage_per_client = models.IntegerField(default=1)
    
    # Conditions
    minimum_transaction_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    applicable_payment_methods = models.JSONField(default=list)
    applicable_fee_types = models.JSONField(default=list)
    
    # Status
    status = models.CharField(max_length=20, choices=PROMO_STATUS, default='ACTIVE')
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=100)

    class Meta:
        managed = True
        db_table = 'promotional_fees'
        indexes = [
            models.Index(fields=['promo_code']),
            models.Index(fields=['client_id', 'status']),
        ]

    def __str__(self):
        return f"{self.promo_code} - {self.promo_name}"

    @property
    def is_valid(self):
        now = timezone.now()
        return (
            self.status == 'ACTIVE' and
            self.valid_from <= now <= self.valid_until and
            self.used_count < self.usage_limit
        )

    def apply_discount(self, fee_amount, transaction_amount=None):
        """Apply promotional discount to fee amount"""
        if not self.is_valid:
            raise ValueError("Promotional code is not valid")
        
        if self.minimum_transaction_amount and transaction_amount:
            if Decimal(str(transaction_amount)) < self.minimum_transaction_amount:
                raise ValueError(f"Minimum transaction amount of {self.minimum_transaction_amount} required")
        
        if self.discount_type == 'PERCENTAGE':
            discount = fee_amount * self.discount_value / 100
        elif self.discount_type == 'FLAT':
            discount = min(self.discount_value, fee_amount)
        elif self.discount_type == 'WAIVER':
            discount = fee_amount
        else:  # CASHBACK
            discount = min(self.discount_value, fee_amount)
        
        if self.max_discount_amount:
            discount = min(discount, self.max_discount_amount)
        
        return discount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


class FeeReconciliation(models.Model):
    RECON_STATUS = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('DISCREPANCY', 'Discrepancy Found'),
        ('RESOLVED', 'Resolved')
    ]
    
    recon_id = models.AutoField(primary_key=True)
    period = models.CharField(max_length=20)  # "2024-01", "2024-Q1", etc.
    client_id = models.CharField(max_length=50)
    
    # Fee totals
    total_transactions = models.IntegerField(default=0)
    total_transaction_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_fees_charged = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_fees_collected = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Calculated vs actual
    calculated_fees = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    variance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    variance_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Breakdown by fee type
    fee_breakdown = models.JSONField(default=dict)
    
    # Discrepancies
    discrepancy_details = models.JSONField(default=list)
    discrepancy_count = models.IntegerField(default=0)
    
    # Status
    status = models.CharField(max_length=20, choices=RECON_STATUS, default='PENDING')
    reconciled_at = models.DateTimeField(null=True, blank=True)
    reconciled_by = models.CharField(max_length=100, null=True, blank=True)
    
    # Notes
    notes = models.TextField(null=True, blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'fee_reconciliation'
        unique_together = ['period', 'client_id']
        indexes = [
            models.Index(fields=['client_id', 'period']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Recon {self.recon_id}: {self.client_id} - {self.period}"

    def calculate_variance(self):
        """Calculate variance between calculated and collected fees"""
        self.variance = self.total_fees_collected - self.calculated_fees
        if self.calculated_fees != 0:
            self.variance_percentage = (self.variance / self.calculated_fees) * 100
        else:
            self.variance_percentage = 0
        
        if abs(self.variance) > Decimal('0.01'):
            self.status = 'DISCREPANCY'
        else:
            self.status = 'COMPLETED'
        
        self.save()