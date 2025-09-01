from django.db import models
from django.utils import timezone
from decimal import Decimal
import uuid

class TransactionDetail(models.Model):
    """Reference to main transaction table"""
    txn_id = models.CharField(max_length=100, primary_key=True)
    client_id = models.IntegerField()
    client_name = models.CharField(max_length=200)
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2)
    bank_txn_id = models.CharField(max_length=100, null=True)
    status = models.CharField(max_length=50)
    created_date = models.DateTimeField()
    reconciliation_date = models.DateTimeField(null=True)
    
    class Meta:
        db_table = 'transaction_detail'
        managed = False

class TransactionReconTable(models.Model):
    """Main reconciliation tracking table - EXISTS IN DB!"""
    recon_id = models.AutoField(primary_key=True)
    txn_id = models.CharField(max_length=100)
    client_id = models.IntegerField()
    transaction_amount = models.DecimalField(max_digits=15, decimal_places=2)
    bank_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    recon_status = models.CharField(max_length=20)  # PENDING, MATCHED, MISMATCHED, MANUAL
    recon_date = models.DateTimeField(null=True)
    bank_reference = models.CharField(max_length=100, null=True)
    bank_date = models.DateField(null=True)
    remarks = models.TextField(null=True)
    matched_by = models.CharField(max_length=20, null=True)  # AUTO, MANUAL
    matched_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'transaction_recon_table'
        managed = True

class BankStatementUpload(models.Model):
    """Track bank statement uploads"""
    upload_id = models.AutoField(primary_key=True)
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    bank_name = models.CharField(max_length=100)
    statement_date = models.DateField()
    uploaded_by = models.CharField(max_length=100)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    total_records = models.IntegerField(default=0)
    matched_records = models.IntegerField(default=0)
    mismatched_records = models.IntegerField(default=0)
    status = models.CharField(max_length=20, default='UPLOADED')  # UPLOADED, PROCESSING, COMPLETED
    
    class Meta:
        db_table = 'bank_statement_uploads'
        managed = True

class BankStatementEntry(models.Model):
    """Individual bank statement entries"""
    entry_id = models.AutoField(primary_key=True)
    upload_id = models.ForeignKey(BankStatementUpload, on_delete=models.CASCADE)
    transaction_date = models.DateField()
    value_date = models.DateField()
    description = models.TextField()
    reference_number = models.CharField(max_length=100)
    debit_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    credit_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    balance = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    transaction_type = models.CharField(max_length=50)  # CREDIT, DEBIT
    matched_txn_id = models.CharField(max_length=100, null=True)
    match_status = models.CharField(max_length=20, default='UNMATCHED')
    match_confidence = models.IntegerField(null=True)  # Percentage confidence
    
    class Meta:
        db_table = 'bank_statement_entries'
        managed = True

class ReconciliationMismatch(models.Model):
    """Track reconciliation mismatches"""
    mismatch_id = models.AutoField(primary_key=True)
    txn_id = models.CharField(max_length=100, null=True)
    bank_entry_id = models.ForeignKey(BankStatementEntry, on_delete=models.CASCADE, null=True)
    mismatch_type = models.CharField(max_length=50)  # AMOUNT, DATE, MISSING_IN_BANK, MISSING_IN_SYSTEM
    system_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    bank_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    difference = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    system_date = models.DateField(null=True)
    bank_date = models.DateField(null=True)
    status = models.CharField(max_length=20, default='OPEN')  # OPEN, INVESTIGATING, RESOLVED
    resolution = models.TextField(null=True)
    resolved_by = models.CharField(max_length=100, null=True)
    resolved_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'reconciliation_mismatches'
        managed = True

class ReconciliationRule(models.Model):
    """Rules for auto-matching"""
    rule_id = models.AutoField(primary_key=True)
    rule_name = models.CharField(max_length=100)
    rule_type = models.CharField(max_length=50)  # EXACT, FUZZY, PATTERN
    match_field = models.CharField(max_length=50)  # AMOUNT, REFERENCE, DATE_RANGE
    tolerance_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    tolerance_days = models.IntegerField(null=True)
    pattern = models.CharField(max_length=255, null=True)
    priority = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'reconciliation_rules'
        managed = True
