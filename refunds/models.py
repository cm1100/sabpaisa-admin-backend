from django.db import models
from django.utils import timezone
from decimal import Decimal
import uuid

class TransactionDetail(models.Model):
    """Reference to main transaction table with refund fields"""
    txn_id = models.CharField(max_length=100, primary_key=True)
    client_id = models.IntegerField()
    client_name = models.CharField(max_length=200)
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2)
    settlement_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    status = models.CharField(max_length=50)
    
    # Refund-related fields that exist in DB
    refund_status_code = models.CharField(max_length=20, null=True)
    refund_date = models.CharField(max_length=100, null=True)
    refunded_date = models.DateTimeField(null=True)
    refund_message = models.TextField(null=True)
    refund_reason = models.CharField(max_length=500, null=True)
    refunded_amount = models.FloatField(null=True)
    refund_amount = models.FloatField(null=True)
    refund_track_id = models.CharField(max_length=100, null=True)
    refund_initiated_on = models.DateTimeField(null=True)
    refund_process_on = models.DateTimeField(null=True)
    refund_request_from = models.CharField(max_length=100, null=True)
    
    @property
    def is_refunded(self):
        """Check if transaction has been refunded based on refund fields"""
        return bool(self.refunded_date or self.refund_status_code == 'COMPLETED')
    
    # Settlement fields
    is_settled = models.BooleanField(default=False)
    settlement_date = models.DateTimeField(null=True)
    
    trans_date = models.DateTimeField()
    
    @property
    def created_date(self):
        """Alias for trans_date for compatibility"""
        return self.trans_date
    
    class Meta:
        db_table = 'transaction_detail'
        managed = False

class RefundRequestFromClient(models.Model):
    """Main refund request table - EXISTS IN DB!"""
    refund_id = models.AutoField(primary_key=True)
    amount = models.CharField(max_length=100, null=True)
    client_code = models.CharField(max_length=100, null=True)
    client_id = models.CharField(max_length=100, null=True)
    client_txn_id = models.CharField(max_length=100, null=True)
    message = models.TextField(null=True)
    refund_complete_date = models.DateTimeField(null=True)
    refund_init_date = models.DateTimeField(null=True)
    sp_txn_id = models.CharField(max_length=100, null=True)
    login_id = models.IntegerField(null=True)
    refunded_bank_ref_id = models.CharField(max_length=100, null=True)
    
    # Additional fields we'll use virtually (not in DB)
    @property
    def refund_type(self):
        return 'FULL'  # Default to FULL
    
    @property 
    def status(self):
        if self.refund_complete_date:
            return 'COMPLETED'
        elif self.refund_init_date:
            return 'PROCESSING'
        return 'PENDING'
    
    @property
    def requested_by(self):
        return f"User_{self.login_id}" if self.login_id else 'Unknown'
    
    class Meta:
        db_table = 'refund_request_from_client'
        managed = False

class RefundApprovalWorkflow(models.Model):
    """Refund approval workflow tracking"""
    workflow_id = models.AutoField(primary_key=True)
    refund_id = models.IntegerField()
    stage = models.CharField(max_length=50)  # INITIATED, L1_APPROVAL, L2_APPROVAL, FINANCE_APPROVAL, COMPLETED
    action = models.CharField(max_length=20)  # APPROVE, REJECT, ESCALATE
    action_by = models.CharField(max_length=100)
    action_date = models.DateTimeField(auto_now_add=True)
    comments = models.TextField(null=True)
    next_stage = models.CharField(max_length=50, null=True)
    
    class Meta:
        db_table = 'refund_approval_workflow'
        managed = True

class RefundConfiguration(models.Model):
    """Refund configuration per client"""
    config_id = models.AutoField(primary_key=True)
    client_id = models.IntegerField(unique=True)
    refund_allowed = models.BooleanField(default=True)
    partial_refund_allowed = models.BooleanField(default=False)
    max_refund_days = models.IntegerField(default=180)
    min_refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    max_refund_amount = models.DecimalField(max_digits=12, decimal_places=2, default=500000)
    auto_approve_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    requires_l1_approval = models.BooleanField(default=True)
    requires_l2_approval = models.BooleanField(default=True)
    requires_finance_approval = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'refund_configuration'
        managed = True

class RefundBatch(models.Model):
    """Batch processing of refunds"""
    batch_id = models.AutoField(primary_key=True)
    batch_reference = models.CharField(max_length=100, unique=True)
    total_refunds = models.IntegerField()
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=20, default='CREATED')  # CREATED, PROCESSING, COMPLETED, FAILED
    file_path = models.CharField(max_length=500, null=True)
    created_by = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True)
    
    class Meta:
        db_table = 'refund_batch'
        managed = True

class RefundBatchItem(models.Model):
    """Individual items in refund batch"""
    item_id = models.AutoField(primary_key=True)
    batch = models.ForeignKey(RefundBatch, on_delete=models.CASCADE)
    refund_id = models.IntegerField()
    txn_id = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=20, default='PENDING')
    pg_response = models.JSONField(null=True)
    processed_at = models.DateTimeField(null=True)
    
    class Meta:
        db_table = 'refund_batch_items'
        managed = True

class RefundSettlementAdjustment(models.Model):
    """Track settlement adjustments for refunds"""
    adjustment_id = models.AutoField(primary_key=True)
    refund_id = models.IntegerField()
    txn_id = models.CharField(max_length=100)
    original_settlement_amount = models.DecimalField(max_digits=15, decimal_places=2)
    refund_amount = models.DecimalField(max_digits=15, decimal_places=2)
    adjusted_settlement_amount = models.DecimalField(max_digits=15, decimal_places=2)
    adjustment_type = models.CharField(max_length=20)  # DEBIT, CREDIT
    settlement_date = models.DateField()
    adjusted_on = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'refund_settlement_adjustments'
        managed = True
