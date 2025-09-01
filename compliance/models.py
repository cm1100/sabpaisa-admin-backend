from django.db import models
from django.utils import timezone
from django.contrib.postgres.fields import JSONField


class TransactionDetail(models.Model):
    """Reference for suspicious transaction detection"""
    txn_id = models.CharField(max_length=100, primary_key=True)
    client_id = models.IntegerField()
    client_name = models.CharField(max_length=200)
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2)
    payment_mode = models.CharField(max_length=50)
    status = models.CharField(max_length=50)
    kyc_status = models.CharField(max_length=20, null=True)
    risk_score = models.IntegerField(null=True)
    payee_email = models.EmailField(max_length=200, null=True)
    payee_mob = models.CharField(max_length=15, null=True)
    ip_address = models.GenericIPAddressField(null=True)
    created_date = models.DateTimeField()
    
    class Meta:
        db_table = 'transaction_detail'
        managed = False


class ClientDataTable(models.Model):
    """Client KYC information"""
    client_id = models.AutoField(primary_key=True)
    client_code = models.CharField(max_length=50)
    client_name = models.CharField(max_length=200)
    kyc_status = models.CharField(max_length=20, default='PENDING')
    kyc_verified_date = models.DateTimeField(null=True)
    risk_category = models.CharField(max_length=20, default='LOW')
    pan_number = models.CharField(max_length=10)
    gst_number = models.CharField(max_length=15, null=True)
    agreement_status = models.CharField(max_length=20, default='PENDING')
    agreement_date = models.DateField(null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField()
    
    class Meta:
        db_table = 'client_data_table'
        managed = False


class AdminUserActivityLog(models.Model):
    """Complete audit trail"""
    log_id = models.AutoField(primary_key=True)
    user_id = models.IntegerField()
    activity = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(null=True)
    entity_type = models.CharField(max_length=50, null=True)
    entity_id = models.CharField(max_length=100, null=True)
    
    class Meta:
        db_table = 'admin_user_activity_log'
        managed = False


class ComplianceAlert(models.Model):
    """Compliance alerts and flags"""
    alert_id = models.AutoField(primary_key=True)
    alert_type = models.CharField(max_length=50)  # SUSPICIOUS_TXN, HIGH_VALUE, VELOCITY, KYC_EXPIRED
    severity = models.CharField(max_length=20)  # HIGH, MEDIUM, LOW
    entity_type = models.CharField(max_length=50)  # TRANSACTION, CLIENT
    entity_id = models.CharField(max_length=100)
    description = models.TextField()
    detected_at = models.DateTimeField(auto_now_add=True)
    reviewed = models.BooleanField(default=False)
    reviewed_by = models.CharField(max_length=100, null=True)
    reviewed_at = models.DateTimeField(null=True)
    action_taken = models.TextField(null=True)
    status = models.CharField(max_length=20, default='OPEN')  # OPEN, UNDER_REVIEW, RESOLVED, ESCALATED
    metadata = models.JSONField(null=True)
    
    class Meta:
        db_table = 'compliance_alerts'
        managed = True  # We'll create this table


class RBIReportLog(models.Model):
    """RBI report generation log"""
    report_id = models.AutoField(primary_key=True)
    report_type = models.CharField(max_length=50)  # DAILY, WEEKLY, MONTHLY, QUARTERLY
    report_period_start = models.DateField()
    report_period_end = models.DateField()
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.CharField(max_length=100)
    file_path = models.CharField(max_length=500)
    status = models.CharField(max_length=20)  # GENERATED, SUBMITTED, ACKNOWLEDGED
    submission_ref = models.CharField(max_length=100, null=True)
    
    class Meta:
        db_table = 'rbi_report_log'
        managed = True
