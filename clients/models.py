"""
Client Models - Following Single Responsibility Principle
Each model handles one specific aspect of client data
"""
from django.db import models
from django.utils import timezone


class ClientDataTable(models.Model):
    """
    Main client data model - migrated from existing database
    Single Responsibility: Manages core client information
    """
    client_id = models.IntegerField(primary_key=True)
    active = models.BooleanField(default=False, blank=True, null=True)
    auth_flag = models.BooleanField(default=True, blank=True, null=True)
    auth_key = models.TextField()
    auth_type = models.TextField(blank=True, null=True)
    client_code = models.TextField(unique=True, blank=True, null=True)
    client_contact = models.TextField()
    client_email = models.TextField(blank=True, null=True)
    auth_iv = models.TextField()
    client_name = models.TextField()
    client_pass = models.TextField()
    client_type = models.TextField(blank=True, null=True)
    client_user_name = models.TextField()
    created_by = models.TextField(blank=True, null=True)
    creation_date = models.DateTimeField(blank=True, null=True)
    enquiry_flag = models.BooleanField(default=False, blank=True, null=True)
    failed_ru_url = models.TextField()
    is_application = models.BooleanField(default=False, blank=True, null=True)
    push_api_flag = models.BooleanField(default=False, blank=True, null=True)
    push_api_url = models.TextField()
    refund_applicable = models.BooleanField(default=False, blank=True, null=True)
    success_ru_url = models.TextField()
    ui_by_pass = models.BooleanField(default=False, blank=True, null=True)
    update_date = models.DateTimeField(blank=True, null=True)
    update_by = models.TextField(blank=True, null=True)
    partner_bank_id = models.IntegerField(blank=True, null=True)
    client_logo_path = models.TextField()
    client_address = models.TextField(blank=True, null=True)
    applicable_for_challan = models.CharField(max_length=45, blank=True, null=True)
    application_appid = models.IntegerField(db_column='application_appId', blank=True, null=True)
    is_refund_applicable = models.TextField(blank=True, null=True)
    loginbean_loginid = models.IntegerField(db_column='loginBean_loginId', blank=True, null=True)
    redirect_to_new_layout = models.TextField(blank=True, null=True)
    duplicate_restriction = models.BooleanField(default=False, blank=True, null=True)
    donation_flag = models.BooleanField(default=False, blank=True, null=True)
    round_off = models.BooleanField(default=True, blank=True, null=True)
    refund_type = models.TextField(blank=True, null=True)
    risk_category = models.IntegerField(blank=True, null=True)
    ispaybylink = models.SmallIntegerField(db_column='isPaybyLink', blank=True, null=True)
    ispaybyform = models.SmallIntegerField(db_column='isPaybyForm', blank=True, null=True)
    mesaage_bypass_flag = models.BooleanField(default=False, blank=True, null=True)
    van_flag = models.BooleanField(default=False, blank=True, null=True)
    tpv_flag = models.BooleanField(default=False, blank=True, null=True)
    abort_job_flag = models.BooleanField(default=False, blank=True, null=True)
    gift_card_flag = models.BooleanField(default=False, blank=True, null=True)
    is_client_logo_flag = models.SmallIntegerField(blank=True, null=True)
    is_commercial_flag = models.SmallIntegerField(blank=True, null=True)
    is_partnerbank_logo_flag = models.SmallIntegerField(blank=True, null=True)
    is_whitelisted = models.BooleanField(default=False, blank=True, null=True)
    api_version = models.IntegerField(blank=True, null=True)
    
    class Meta:
        managed = False  # Don't create migrations for existing table
        db_table = 'client_data_table'
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'
        ordering = ['-creation_date']
    
    def __str__(self):
        return f"{self.client_name} ({self.client_code})"
    
    @property
    def is_active(self):
        """Property to check if client is active"""
        return self.active
    
    def activate(self):
        """Method to activate client - Single Responsibility"""
        self.active = True
        self.update_date = timezone.now()
        self.save(update_fields=['active', 'update_date'])
    
    def deactivate(self):
        """Method to deactivate client - Single Responsibility"""
        self.active = False
        self.update_date = timezone.now()
        self.save(update_fields=['active', 'update_date'])


class ClientPaymentMode(models.Model):
    """
    Client payment mode configuration
    Single Responsibility: Manages payment mode settings per client
    """
    client_paymode_id = models.IntegerField(primary_key=True)
    paymode_flag = models.BooleanField(blank=True, null=True)
    payment_mode_id = models.IntegerField(blank=True, null=True)
    payment_mode_name = models.TextField(blank=True, null=True)
    client_data_client_id = models.IntegerField(blank=True, null=True)
    is_frm_applicable = models.BooleanField(default=False)
    
    class Meta:
        managed = False
        db_table = 'client_payment_mode'
        verbose_name = 'Client Payment Mode'
        verbose_name_plural = 'Client Payment Modes'
    
    def __str__(self):
        return f"Client {self.client_id} - {self.payment_mode}"


class ClientFeeBearer(models.Model):
    """
    Fee bearer configuration for clients
    Single Responsibility: Manages who bears the transaction fee
    """
    id = models.AutoField(primary_key=True)
    client_code = models.CharField(max_length=10, blank=True, null=True)
    trans_date = models.DateField(blank=True, null=True)
    paymode_id = models.CharField(max_length=5, blank=True, null=True)
    fee_bearer_id = models.CharField(max_length=10, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    referral_id = models.IntegerField(blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = 'client_fee_bearer'
        verbose_name = 'Client Fee Bearer'
        verbose_name_plural = 'Client Fee Bearers'
    
    def __str__(self):
        return f"Client {self.client_id} - {self.paymode} - Bearer: {self.bearer}"