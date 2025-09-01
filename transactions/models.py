"""
Transaction Models - Production Ready
Based on actual SabPaisa database schema with 106 fields
Following SOLID principles and 2025 best practices
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid

User = get_user_model()


class TransactionDetail(models.Model):
    """
    Main transaction model mapped to existing transaction_detail table.
    Contains all 106 fields from the actual database.
    This is the heart of the payment system.
    """
    
    # Transaction Identification Fields
    txn_id = models.CharField(max_length=255, primary_key=True, db_column='txn_id')
    client_txn_id = models.CharField(max_length=255, blank=True, null=True)
    pg_txn_id = models.CharField(max_length=255, blank=True, null=True)
    bank_txn_id = models.CharField(max_length=255, blank=True, null=True)
    bank_txn_id_alt = models.CharField(max_length=255, blank=True, null=True, db_column='bankTxnId')
    transaction_tracker_id = models.CharField(max_length=255, blank=True, null=True)
    challan_no = models.CharField(max_length=255, blank=True, null=True)
    arn = models.CharField(max_length=255, blank=True, null=True)
    treasury_bank_scroll_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Client Linkage Fields
    client_id = models.CharField(max_length=255, blank=True, null=True)
    client_code = models.CharField(max_length=255, blank=True, null=True)
    client_name = models.CharField(max_length=255, blank=True, null=True)
    mapping_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Amount Fields (Complete Money Flow)
    payee_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    paid_amount = models.FloatField(blank=True, null=True)
    act_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    pg_return_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    donation_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    
    # Fee Structure
    convcharges = models.FloatField(blank=True, null=True)
    ep_charges = models.FloatField(blank=True, null=True)
    gst = models.FloatField(blank=True, null=True)
    conv_gst = models.FloatField(blank=True, null=True)
    endpoint_gst = models.FloatField(blank=True, null=True)
    sp_conv_rate = models.DecimalField(max_digits=5, decimal_places=4, blank=True, null=True)
    ep_conv_rate = models.DecimalField(max_digits=5, decimal_places=4, blank=True, null=True)
    sp_conv_rate_type = models.CharField(max_length=20, blank=True, null=True)
    ep_conv_rate_type = models.CharField(max_length=20, blank=True, null=True)
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    gst_rate_type = models.CharField(max_length=20, blank=True, null=True)
    mandate_charges = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    # Settlement Amounts
    settlement_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    effective_settlement_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    settlement_bank_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    rolling_reserve_plus = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    rolling_reserve_minus = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    
    # Payment Information
    payment_mode = models.CharField(max_length=50, blank=True, null=True)
    pg_pay_mode = models.CharField(max_length=50, blank=True, null=True)
    payment_mode_id = models.CharField(max_length=50, blank=True, null=True)
    endpoint_id = models.CharField(max_length=50, blank=True, null=True)
    pg_name = models.CharField(max_length=255, blank=True, null=True)
    bank_name = models.CharField(max_length=255, blank=True, null=True)
    card_brand = models.CharField(max_length=50, blank=True, null=True)
    vpa = models.CharField(max_length=255, blank=True, null=True)
    vpa_remarks = models.TextField(blank=True, null=True)
    
    # Customer Details
    payee_first_name = models.CharField(max_length=255, blank=True, null=True)
    payee_mid_name = models.CharField(max_length=255, blank=True, null=True)
    payee_lst_name = models.CharField(max_length=255, blank=True, null=True)
    payee_email = models.EmailField(max_length=255, blank=True, null=True)
    payee_mob = models.CharField(max_length=20, blank=True, null=True)
    reg_number = models.CharField(max_length=255, blank=True, null=True)
    program_id = models.CharField(max_length=255, blank=True, null=True)
    uit_application_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Status Tracking Fields
    status = models.CharField(max_length=50, blank=True, null=True)
    pg_response_code = models.CharField(max_length=50, blank=True, null=True)
    pag_response_code = models.CharField(max_length=50, blank=True, null=True)
    sabpaisa_resp_code = models.CharField(max_length=50, blank=True, null=True)
    sabpaisa_errorcode = models.CharField(max_length=50, blank=True, null=True)
    bank_errorcode = models.CharField(max_length=50, blank=True, null=True)
    resp_msg = models.TextField(blank=True, null=True)
    bank_message = models.TextField(blank=True, null=True)
    terminal_status = models.CharField(max_length=50, blank=True, null=True)
    
    # Settlement Tracking (CRITICAL)
    is_settled = models.BooleanField(default=False)
    settlement_date = models.DateTimeField(blank=True, null=True)
    settlement_status = models.CharField(max_length=50, blank=True, null=True)
    settlement_by = models.CharField(max_length=255, blank=True, null=True)
    settlement_bank_ref = models.CharField(max_length=255, blank=True, null=True)
    settlement_remarks = models.TextField(blank=True, null=True)
    settlement_utr = models.CharField(max_length=255, blank=True, null=True)
    settlement_bank_amount_date = models.DateTimeField(blank=True, null=True)
    settlepaisa_data = models.BooleanField(default=False)
    
    # Refund Management
    refund_status_code = models.CharField(max_length=50, blank=True, null=True)
    refund_date = models.DateTimeField(blank=True, null=True)
    refunded_date = models.DateTimeField(blank=True, null=True)
    refund_message = models.TextField(blank=True, null=True)
    refund_reason = models.TextField(blank=True, null=True)
    refunded_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    refund_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    refund_track_id = models.CharField(max_length=255, blank=True, null=True)
    refund_initiated_on = models.DateTimeField(blank=True, null=True)
    refund_process_on = models.DateTimeField(blank=True, null=True)
    refund_request_from = models.CharField(max_length=255, blank=True, null=True)
    
    # Chargeback Handling
    is_charge_back = models.BooleanField(default=False)
    charge_back_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    charge_back_date = models.DateTimeField(blank=True, null=True)
    charge_back_status = models.CharField(max_length=50, blank=True, null=True)
    charge_back_debit_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    charge_back_credit_date_to_merchant = models.DateTimeField(blank=True, null=True)
    charge_back_remarks = models.TextField(blank=True, null=True)
    chargeback_request_from = models.CharField(max_length=255, blank=True, null=True)
    bank_cb_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    merchant_cb_status = models.CharField(max_length=50, blank=True, null=True)
    prearb_date = models.DateTimeField(blank=True, null=True)
    cb_credit_date_txn_reject = models.DateTimeField(blank=True, null=True)
    amount_available_to_adjust = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    amount_adjust_on = models.DateTimeField(blank=True, null=True)
    money_asked_from_merchant = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    
    # Timestamps
    trans_date = models.DateTimeField(blank=True, null=True)
    trans_complete_date = models.DateTimeField(blank=True, null=True)
    enquiry_date = models.DateTimeField(blank=True, null=True)
    trans_push_date = models.DateTimeField(blank=True, null=True)
    sent_notification_payer_confirmation_dt = models.DateTimeField(blank=True, null=True)
    payer_confirmation_respones_dt = models.DateTimeField(blank=True, null=True)
    transaction_tracker_time = models.DateTimeField(blank=True, null=True)
    
    # Technical/Tracking Fields
    client_request_ip = models.CharField(max_length=45, blank=True, null=True)
    browser_name = models.CharField(max_length=255, blank=True, null=True, db_column='broser_name')
    browser_details = models.TextField(blank=True, null=True)
    device_name = models.CharField(max_length=255, blank=True, null=True)
    channel_id = models.CharField(max_length=50, blank=True, null=True)
    auth_code = models.CharField(max_length=255, blank=True, null=True)
    force_success_flag = models.BooleanField(default=False)
    bin_update_flag = models.BooleanField(default=False)
    trans_flag = models.BooleanField(default=False)
    trans_push_flag = models.BooleanField(default=False)
    payer_confirmation = models.BooleanField(default=False)
    enquiry_counter = models.IntegerField(default=0)
    payer_confirmation_request_ct = models.IntegerField(default=0)
    
    # URL Management
    application_fail_url = models.URLField(max_length=500, blank=True, null=True)
    application_succ_url = models.URLField(max_length=500, blank=True, null=True)
    sent_notification_payer_confirmation_url = models.URLField(max_length=500, blank=True, null=True)
    
    # Business Fields
    amount_type = models.CharField(max_length=50, blank=True, null=True)
    alert_flag = models.CharField(max_length=10, blank=True, null=True)
    changed_on_followup = models.CharField(max_length=10, blank=True, null=True)
    fee_forward = models.CharField(max_length=10, blank=True, null=True)
    business_ctg_code = models.CharField(max_length=50, blank=True, null=True)
    referral_code = models.CharField(max_length=50, blank=True, null=True)
    trans_updated_by = models.CharField(max_length=255, blank=True, null=True)
    mandate_flag = models.BooleanField(default=False)
    mandate_status = models.CharField(max_length=50, blank=True, null=True)
    
    # UDF Fields
    udf19 = models.TextField(blank=True, null=True)
    udf20 = models.TextField(blank=True, null=True)
    
    class Meta:
        managed = False  # Don't manage this table as it exists
        db_table = 'transaction_detail'
        ordering = ['-trans_date']
        indexes = [
            models.Index(fields=['-trans_date']),
            models.Index(fields=['client_code']),
            models.Index(fields=['status']),
            models.Index(fields=['is_settled']),
            models.Index(fields=['payment_mode']),
        ]
    
    def __str__(self):
        return f"Transaction {self.txn_id} - ₹{self.paid_amount or 0}"
    
    @property
    def is_successful(self):
        """Check if transaction was successful"""
        return self.status and self.status.upper() == 'SUCCESS'
    
    @property
    def formatted_amount(self):
        """Return formatted amount with currency"""
        amount = self.paid_amount or self.act_amount or 0.00
        return f"₹{amount:,.2f}"
    
    @property
    def total_fees(self):
        """Calculate total fees including GST"""
        fees = 0.00
        if self.convcharges:
            fees += self.convcharges
        if self.ep_charges:
            fees += self.ep_charges
        if self.gst:
            fees += self.gst
        if self.conv_gst:
            fees += self.conv_gst
        if self.endpoint_gst:
            fees += self.endpoint_gst
        return fees
    
    @property
    def net_settlement_amount(self):
        """Calculate net settlement amount after fees"""
        if self.settlement_amount:
            return self.settlement_amount
        if self.paid_amount:
            return self.paid_amount - self.total_fees
        return Decimal('0.00')
    
    @property
    def customer_name(self):
        """Get full customer name"""
        parts = []
        if self.payee_first_name:
            parts.append(self.payee_first_name)
        if self.payee_mid_name:
            parts.append(self.payee_mid_name)
        if self.payee_lst_name:
            parts.append(self.payee_lst_name)
        return ' '.join(parts) or 'Unknown'
    
    @property
    def is_refundable(self):
        """Check if transaction can be refunded"""
        if not self.is_successful:
            return False
        if self.refund_status_code and self.refund_status_code.upper() in ['COMPLETED', 'PROCESSING']:
            return False
        if self.refunded_amount and self.refunded_amount >= (self.paid_amount or 0):
            return False
        return True
    
    @property
    def has_chargeback(self):
        """Check if transaction has chargeback"""
        return self.is_charge_back or bool(self.charge_back_amount)


class SettledTransactions(models.Model):
    """
    Settlement records for completed transactions
    Maps to settled_transactions table
    """
    id = models.BigAutoField(primary_key=True)
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    bank_name = models.CharField(max_length=255, blank=True, null=True)
    transaction_mode = models.CharField(max_length=50, blank=True, null=True)
    trans_date = models.DateField(blank=True, null=True)
    net_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    gross_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    currency = models.CharField(max_length=3, default='INR')
    conv_fee = models.CharField(max_length=50, blank=True, null=True)
    gst_fee = models.CharField(max_length=50, blank=True, null=True)
    pipe_fee = models.CharField(max_length=50, blank=True, null=True)
    transaction_status = models.CharField(max_length=50, blank=True, null=True)
    payout_status = models.BooleanField(default=False)
    name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    mobile_number = models.CharField(max_length=20, blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=255, blank=True, null=True)
    company_domain = models.CharField(max_length=255, blank=True, null=True)
    settlement_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    payment_date = models.DateField(blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = 'settled_transactions'
        ordering = ['-trans_date']
    
    def __str__(self):
        return f"Settlement {self.transaction_id} - ₹{self.net_amount or 0}"


class TransactionReconTable(models.Model):
    """
    Reconciliation table for matching bank statements
    """
    recon_id = models.BigAutoField(primary_key=True)
    txn_id = models.CharField(max_length=255, blank=True, null=True)
    bank_ref = models.CharField(max_length=255, blank=True, null=True)
    bank_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    our_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    difference = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    recon_date = models.DateTimeField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = 'transaction_recon_table'
        ordering = ['-recon_date']
    
    def __str__(self):
        return f"Recon {self.recon_id} - {self.txn_id}"


class TransactionsToSettle(models.Model):
    """
    Queue for pending settlement transactions
    Maps to transactions_to_settle table
    """
    id = models.BigAutoField(primary_key=True)
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    pg_name = models.CharField(max_length=255, blank=True, null=True)
    pg_pay_mode = models.CharField(max_length=50, blank=True, null=True)
    bank_name = models.CharField(max_length=255, blank=True, null=True)
    act_amount = models.FloatField(blank=True, null=True)
    client_code = models.CharField(max_length=255, blank=True, null=True)
    payee_name = models.CharField(max_length=255, blank=True, null=True)
    payee_email = models.CharField(max_length=255, blank=True, null=True)
    payee_mobile = models.CharField(max_length=20, blank=True, null=True)
    payee_amount = models.FloatField(blank=True, null=True)
    paid_amount = models.FloatField(blank=True, null=True)
    payment_mode = models.CharField(max_length=50, blank=True, null=True)
    transaction_mode = models.CharField(max_length=50, blank=True, null=True)
    currency = models.CharField(max_length=3, default='INR')
    convcharges = models.FloatField(blank=True, null=True)
    ep_charges = models.FloatField(blank=True, null=True)
    gst = models.FloatField(blank=True, null=True)
    gst_rate_type = models.CharField(max_length=50, blank=True, null=True)
    gst_rate = models.FloatField(blank=True, null=True)
    conv_gst = models.FloatField(blank=True, null=True)
    endpoint_gst = models.FloatField(blank=True, null=True)
    pipe_fee = models.CharField(max_length=50, blank=True, null=True)
    transaction_status = models.CharField(max_length=50, blank=True, null=True)
    trans_date = models.DateTimeField(blank=True, null=True)
    trans_complete_date = models.DateTimeField(blank=True, null=True)
    payout_status = models.CharField(max_length=50, blank=True, null=True)
    fee_forward = models.CharField(max_length=50, blank=True, null=True)
    sp_conv_rate = models.FloatField(blank=True, null=True)
    sp_conv_rate_type = models.CharField(max_length=50, blank=True, null=True)
    ep_conv_rate = models.FloatField(blank=True, null=True)
    ep_conv_rate_type = models.CharField(max_length=50, blank=True, null=True)
    created_on = models.DateTimeField(blank=True, null=True)
    created_by = models.CharField(max_length=255, blank=True, null=True)
    is_settled = models.CharField(max_length=50, blank=True, null=True)
    settlement_date = models.DateTimeField(blank=True, null=True)
    settlement_amount = models.FloatField(blank=True, null=True)
    settlement_status = models.CharField(max_length=50, blank=True, null=True)
    settlement_by = models.CharField(max_length=255, blank=True, null=True)
    settlement_bank_ref = models.CharField(max_length=255, blank=True, null=True)
    settlement_remarks = models.CharField(max_length=500, blank=True, null=True)
    settlement_utr = models.CharField(max_length=255, blank=True, null=True)
    settlement_bank_amount = models.FloatField(blank=True, null=True)
    settlement_bank_amount_date = models.DateTimeField(blank=True, null=True)
    conv_fee_bearer = models.FloatField(blank=True, null=True)
    is_recon = models.CharField(max_length=50, blank=True, null=True)
    recon_date = models.DateTimeField(blank=True, null=True)
    is_bank_settled = models.CharField(max_length=50, blank=True, null=True)
    is_merchant_settled = models.CharField(max_length=50, blank=True, null=True)
    client_name = models.CharField(max_length=255, blank=True, null=True)
    client_txn_id = models.CharField(max_length=255, blank=True, null=True)
    challan_no = models.CharField(max_length=255, blank=True, null=True)
    bank_txn_id = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = 'transactions_to_settle'
        ordering = ['-trans_date']
    
    def __str__(self):
        return f"To Settle {self.transaction_id} - ₹{self.settlement_amount or 0}"


class RefundRequestFromClient(models.Model):
    """
    Client-initiated refund requests
    Maps to refund_request_from_client table
    """
    refund_id = models.BigAutoField(primary_key=True)
    txn_id = models.CharField(max_length=255, blank=True, null=True)
    client_id = models.CharField(max_length=255, blank=True, null=True)
    refund_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    refund_reason = models.TextField(blank=True, null=True)
    request_date = models.DateTimeField(blank=True, null=True)
    approval_status = models.CharField(max_length=50, blank=True, null=True)
    approved_by = models.CharField(max_length=255, blank=True, null=True)
    approved_date = models.DateTimeField(blank=True, null=True)
    processed_date = models.DateTimeField(blank=True, null=True)
    bank_ref = models.CharField(max_length=255, blank=True, null=True)
    
    APPROVAL_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
    ]
    
    class Meta:
        managed = False
        db_table = 'refund_request_from_client'
        ordering = ['-request_date']
    
    def __str__(self):
        return f"Refund Request {self.refund_id} for {self.txn_id}"