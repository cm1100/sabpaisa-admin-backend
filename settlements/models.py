"""
Settlement Models
Following SOLID principles with proper abstraction
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid
from decimal import Decimal

User = get_user_model()


class SettlementBatch(models.Model):
    """
    Settlement batch for processing multiple transactions
    """
    batch_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch_date = models.DateField(default=timezone.now)
    total_transactions = models.IntegerField(default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    processing_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_settlement_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=50, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('APPROVED', 'Approved'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    class Meta:
        db_table = 'settlement_batches'
        ordering = ['-batch_date', '-created_at']
        indexes = [
            models.Index(fields=['-batch_date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Batch {self.batch_id} - {self.batch_date}"
    
    def calculate_net_amount(self):
        """Calculate net settlement amount after fees"""
        self.net_settlement_amount = self.total_amount - self.processing_fee - self.gst_amount
        return self.net_settlement_amount


class SettlementDetail(models.Model):
    """
    Individual settlement record for each transaction
    """
    settlement_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(SettlementBatch, on_delete=models.CASCADE, related_name='settlements')
    txn_id = models.CharField(max_length=255)
    client_code = models.CharField(max_length=100)
    transaction_amount = models.DecimalField(max_digits=10, decimal_places=2)
    settlement_amount = models.DecimalField(max_digits=10, decimal_places=2)
    processing_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    gst_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2)
    settlement_date = models.DateTimeField(null=True, blank=True)
    settlement_status = models.CharField(max_length=50, default='PENDING')
    bank_reference = models.CharField(max_length=150, blank=True)
    utr_number = models.CharField(max_length=150, blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('SETTLED', 'Settled'),
        ('FAILED', 'Failed'),
        ('ON_HOLD', 'On Hold'),
    ]
    
    class Meta:
        db_table = 'settlement_details'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['client_code']),
            models.Index(fields=['settlement_status']),
            models.Index(fields=['txn_id']),
        ]
    
    def __str__(self):
        return f"Settlement {self.settlement_id} - {self.txn_id}"
    
    def calculate_net_amount(self):
        """Calculate net amount after deductions"""
        self.net_amount = self.settlement_amount - self.processing_fee - self.gst_amount
        return self.net_amount


class SettlementReport(models.Model):
    """
    Settlement report generation and tracking
    """
    report_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(SettlementBatch, on_delete=models.CASCADE, related_name='reports')
    report_type = models.CharField(max_length=50)
    report_date = models.DateField(default=timezone.now)
    file_path = models.CharField(max_length=500, blank=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    
    REPORT_TYPE_CHOICES = [
        ('DAILY', 'Daily Settlement'),
        ('WEEKLY', 'Weekly Settlement'),
        ('MONTHLY', 'Monthly Settlement'),
        ('RECONCILIATION', 'Reconciliation'),
        ('SUMMARY', 'Summary Report'),
    ]
    
    class Meta:
        db_table = 'settlement_reports'
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"Report {self.report_id} - {self.report_type}"


class SettlementConfiguration(models.Model):
    """
    Settlement configuration for clients
    """
    config_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client_code = models.CharField(max_length=100, unique=True)
    settlement_cycle = models.CharField(max_length=50, default='T+1')
    min_settlement_amount = models.DecimalField(max_digits=10, decimal_places=2, default=100)
    processing_fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=2.0)
    gst_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=18.0)
    auto_settle = models.BooleanField(default=True)
    bank_account_number = models.CharField(max_length=50, blank=True)
    bank_name = models.CharField(max_length=200, blank=True)
    ifsc_code = models.CharField(max_length=20, blank=True)
    account_holder_name = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    CYCLE_CHOICES = [
        ('T+0', 'Same Day'),
        ('T+1', 'Next Day'),
        ('T+2', 'Two Days'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
    ]
    
    class Meta:
        db_table = 'settlement_configurations'
        ordering = ['client_code']
    
    def __str__(self):
        return f"Config for {self.client_code} - {self.settlement_cycle}"
    
    def calculate_fees(self, amount):
        """Calculate processing fee and GST for an amount"""
        processing_fee = (amount * self.processing_fee_percentage) / 100
        gst = (processing_fee * self.gst_percentage) / 100
        return {
            'processing_fee': processing_fee,
            'gst': gst,
            'total_deduction': processing_fee + gst,
            'net_amount': amount - processing_fee - gst
        }


class SettlementReconciliation(models.Model):
    """
    Settlement reconciliation tracking
    """
    reconciliation_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(SettlementBatch, on_delete=models.CASCADE, related_name='reconciliations')
    bank_statement_amount = models.DecimalField(max_digits=12, decimal_places=2)
    system_amount = models.DecimalField(max_digits=12, decimal_places=2)
    difference_amount = models.DecimalField(max_digits=10, decimal_places=2)
    reconciliation_status = models.CharField(max_length=50)
    reconciled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    reconciled_at = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('MATCHED', 'Matched'),
        ('MISMATCHED', 'Mismatched'),
        ('INVESTIGATING', 'Investigating'),
        ('RESOLVED', 'Resolved'),
    ]
    
    class Meta:
        db_table = 'settlement_reconciliations'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Reconciliation {self.reconciliation_id}"
    
    def calculate_difference(self):
        """Calculate difference between bank and system amounts"""
        self.difference_amount = self.bank_statement_amount - self.system_amount
        return self.difference_amount