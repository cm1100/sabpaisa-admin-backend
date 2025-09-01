# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class AdminOutApiLogs(models.Model):
    id = models.IntegerField(primary_key=True)
    url = models.CharField(max_length=200)
    method = models.CharField(max_length=10)
    payload = models.TextField(blank=True, null=True)  # This field type is a guess.
    headers = models.TextField(blank=True, null=True)  # This field type is a guess.
    file_url = models.TextField(blank=True, null=True)
    response_status = models.IntegerField(blank=True, null=True)
    response_body = models.TextField(blank=True, null=True)  # This field type is a guess.
    response_time_ms = models.IntegerField(blank=True, null=True)
    called_at = models.DateTimeField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    reference_id = models.CharField(max_length=100, blank=True, null=True)
    triggered_by = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'admin_out_api_logs'


class AdminUserActivityLog(models.Model):
    id = models.IntegerField(primary_key=True)
    user_id = models.CharField(max_length=50, blank=True, null=True)
    path = models.CharField(max_length=200)
    method = models.CharField(max_length=10)
    request_time = models.DateTimeField(blank=True, null=True)
    request_body = models.TextField(blank=True, null=True)
    ip_address = models.CharField(max_length=50, blank=True, null=True)
    user_agent = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'admin_user_activity_log'


class AggregatorMaster(models.Model):
    id = models.IntegerField(primary_key=True)
    agg_code = models.IntegerField(blank=True, null=True)
    agg_name = models.CharField(max_length=45, blank=True, null=True)
    created_on = models.DateTimeField(blank=True, null=True)
    created_by = models.CharField(max_length=45, blank=True, null=True)
    modified_on = models.DateTimeField(blank=True, null=True)
    modified_by = models.CharField(max_length=45, blank=True, null=True)
    is_active = models.CharField(max_length=45, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'aggregator_master'


class ApiUserKeys(models.Model):
    id = models.BigIntegerField(primary_key=True)
    api_user = models.TextField(unique=True)
    aes_key = models.TextField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'api_user_keys'


class AppDataTable(models.Model):
    app_id = models.IntegerField(primary_key=True)
    app_name = models.TextField(blank=True, null=True)
    psuedo_client_id = models.IntegerField(blank=True, null=True)
    appid = models.IntegerField(db_column='appId')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'app_data_table'


class BankMaster(models.Model):
    bank_id = models.AutoField()
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    bank_code = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bank_master'


class BinRulesMaster(models.Model):
    id = models.BigAutoField()
    name = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=100)
    created_by = models.CharField(max_length=100, blank=True, null=True)
    changed_by = models.CharField(max_length=100, blank=True, null=True)
    created_on = models.DateTimeField(blank=True, null=True)
    updated_on = models.DateTimeField(blank=True, null=True)
    type = models.CharField(max_length=100, blank=True, null=True)
    company_domain = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_referral = models.BooleanField(blank=True, null=True)
    referral_name = models.CharField(max_length=255, blank=True, null=True)
    referral_id = models.IntegerField(blank=True, null=True)
    client_id = models.CharField(max_length=50, blank=True, null=True)
    service_type = models.CharField(max_length=10, blank=True, null=True)
    stakeholder_detail = models.CharField(max_length=10, blank=True, null=True)
    business_type = models.CharField(max_length=10, blank=True, null=True)
    stakeholder_type = models.IntegerField(blank=True, null=True)
    aggregator_list = models.CharField(max_length=5, blank=True, null=True)
    service_provider_id = models.CharField(max_length=10, blank=True, null=True)
    bank_commission_type = models.CharField(max_length=100, blank=True, null=True)
    bank_commission_value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    is_gst_include = models.IntegerField(blank=True, null=True)
    is_processing_fee = models.IntegerField(blank=True, null=True)
    processing_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    is_on_us = models.IntegerField(blank=True, null=True)
    rule_id = models.BigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bin_rules_master'


class BinSlabMaster(models.Model):
    id = models.BigAutoField()
    bin_rule_id = models.BigIntegerField(blank=True, null=True)
    slab_max = models.BigIntegerField(blank=True, null=True)
    slab_min = models.IntegerField(blank=True, null=True)
    comission_type = models.CharField(max_length=250, blank=True, null=True)
    comission_value = models.CharField(max_length=250, blank=True, null=True)
    rule_master_id = models.IntegerField(blank=True, null=True)
    handling_charge_type = models.CharField(max_length=20, blank=True, null=True)
    handling_charge = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    alternate_comission_type = models.CharField(max_length=250, blank=True, null=True)
    alternate_comission_value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    comission_condition = models.CharField(max_length=50, blank=True, null=True)
    alternate_handling_charge_type = models.CharField(max_length=20, blank=True, null=True)
    alternate_handling_charge = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    handling_charge_condition = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bin_slab_master'


class BusinessType(models.Model):
    id = models.AutoField()
    business_name = models.CharField(max_length=255, blank=True, null=True)
    status = models.BooleanField(blank=True, null=True)
    code = models.CharField(max_length=5, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'business_type'


class BusinessTypeMaster(models.Model):
    id = models.BigAutoField()
    category_name = models.CharField(max_length=100, blank=True, null=True)
    category_code = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(blank=True, null=True)
    created_by = models.CharField(max_length=100, blank=True, null=True)
    created_on = models.DateTimeField(blank=True, null=True)
    update_by = models.CharField(max_length=100, blank=True, null=True)
    updated_on = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'business_type_master'


class ChallanHistoryTable(models.Model):
    enquiry_id = models.TextField(primary_key=True)
    amount = models.TextField(blank=True, null=True)
    challan_number = models.TextField(blank=True, null=True)
    client_code = models.TextField(blank=True, null=True)
    client_txn_id = models.TextField(blank=True, null=True)
    last_update = models.DateTimeField(blank=True, null=True)
    response_code = models.TextField(blank=True, null=True)
    sp_txn_id = models.TextField(blank=True, null=True)
    update_flag = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'challan_history_table'


class ClientApplication(models.Model):
    app = models.ForeignKey(AppDataTable, models.DO_NOTHING, blank=True, null=True)
    client = models.OneToOneField('ClientDataTable', models.DO_NOTHING, primary_key=True)

    class Meta:
        managed = False
        db_table = 'client_application'


class ClientDataTable(models.Model):
    client_id = models.IntegerField(primary_key=True)
    active = models.BooleanField(blank=True, null=True)
    auth_flag = models.BooleanField(blank=True, null=True)
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
    enquiry_flag = models.BooleanField(blank=True, null=True)
    failed_ru_url = models.TextField()
    is_application = models.BooleanField(blank=True, null=True)
    push_api_flag = models.BooleanField(blank=True, null=True)
    push_api_url = models.TextField()
    refund_applicable = models.BooleanField(blank=True, null=True)
    success_ru_url = models.TextField()
    ui_by_pass = models.BooleanField(blank=True, null=True)
    update_date = models.DateTimeField(blank=True, null=True)
    update_by = models.TextField(blank=True, null=True)
    partner_bank = models.ForeignKey('PartnerBank', models.DO_NOTHING, blank=True, null=True)
    client_logo_path = models.TextField()
    client_address = models.TextField(blank=True, null=True)
    applicable_for_challan = models.CharField(max_length=45, blank=True, null=True)
    application_appid = models.IntegerField(db_column='application_appId', blank=True, null=True)  # Field name made lowercase.
    is_refund_applicable = models.TextField(blank=True, null=True)
    loginbean_loginid = models.IntegerField(db_column='loginBean_loginId', blank=True, null=True)  # Field name made lowercase.
    redirect_to_new_layout = models.TextField(blank=True, null=True)
    duplicate_restriction = models.BooleanField(blank=True, null=True)
    donation_flag = models.BooleanField(blank=True, null=True)
    round_off = models.BooleanField(blank=True, null=True)
    refund_type = models.TextField(blank=True, null=True)
    risk_category = models.IntegerField(blank=True, null=True)
    ispaybylink = models.SmallIntegerField(db_column='isPaybyLink', blank=True, null=True)  # Field name made lowercase.
    ispaybyform = models.SmallIntegerField(db_column='isPaybyForm', blank=True, null=True)  # Field name made lowercase.
    mesaage_bypass_flag = models.BooleanField(blank=True, null=True)
    van_flag = models.BooleanField(blank=True, null=True)
    tpv_flag = models.BooleanField(blank=True, null=True)
    abort_job_flag = models.BooleanField(blank=True, null=True)
    gift_card_flag = models.BooleanField(blank=True, null=True)
    is_client_logo_flag = models.SmallIntegerField(blank=True, null=True)
    is_commercial_flag = models.SmallIntegerField(blank=True, null=True)
    is_partnerbank_logo_flag = models.SmallIntegerField(blank=True, null=True)
    is_whitelisted = models.BooleanField(blank=True, null=True)
    api_version = models.IntegerField(blank=True, null=True)
    is_vpa_verify = models.BooleanField(blank=True, null=True)
    login_id = models.IntegerField(blank=True, null=True)
    client_mcc = models.CharField(max_length=20, blank=True, null=True)
    client_alert_flag = models.BooleanField(blank=True, null=True)
    client_alert_message = models.CharField(max_length=100, blank=True, null=True)
    force_success_flag = models.BooleanField(blank=True, null=True)
    client_disable_flag = models.BooleanField(blank=True, null=True)
    client_disable_message = models.CharField(max_length=250, blank=True, null=True)
    checkout_cancel_btn = models.SmallIntegerField(blank=True, null=True)
    business_ctg_code = models.CharField(max_length=50, blank=True, null=True)
    referral_code = models.CharField(max_length=50, blank=True, null=True)
    refund_day = models.IntegerField(blank=True, null=True)
    is_unicode_allowed = models.SmallIntegerField()
    mandate_flag = models.BooleanField(blank=True, null=True)
    mandate_charges = models.FloatField(blank=True, null=True)
    master_name = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'client_data_table'


class ClientDataTableHistory(models.Model):
    history_id = models.IntegerField(primary_key=True)
    client_id = models.IntegerField(blank=True, null=True)
    active = models.BooleanField(blank=True, null=True)
    auth_flag = models.BooleanField(blank=True, null=True)
    auth_key = models.TextField(blank=True, null=True)
    auth_type = models.TextField(blank=True, null=True)
    client_code = models.TextField(blank=True, null=True)
    client_contact = models.TextField(blank=True, null=True)
    client_email = models.TextField(blank=True, null=True)
    auth_iv = models.TextField(blank=True, null=True)
    client_name = models.TextField(blank=True, null=True)
    client_pass = models.TextField(blank=True, null=True)
    client_type = models.TextField(blank=True, null=True)
    client_user_name = models.TextField(blank=True, null=True)
    created_by = models.TextField(blank=True, null=True)
    creation_date = models.DateTimeField(blank=True, null=True)
    enquiry_flag = models.BooleanField(blank=True, null=True)
    failed_ru_url = models.TextField(blank=True, null=True)
    is_application = models.BooleanField(blank=True, null=True)
    push_api_flag = models.BooleanField(blank=True, null=True)
    push_api_url = models.TextField(blank=True, null=True)
    refund_applicable = models.BooleanField(blank=True, null=True)
    success_ru_url = models.TextField(blank=True, null=True)
    ui_by_pass = models.BooleanField(blank=True, null=True)
    update_date = models.DateTimeField(blank=True, null=True)
    update_by = models.TextField(blank=True, null=True)
    partner_bank_id = models.IntegerField(blank=True, null=True)
    client_logo_path = models.TextField(blank=True, null=True)
    client_address = models.TextField(blank=True, null=True)
    applicable_for_challan = models.CharField(max_length=45, blank=True, null=True)
    application_appid = models.IntegerField(db_column='application_appId', blank=True, null=True)  # Field name made lowercase.
    is_refund_applicable = models.TextField(blank=True, null=True)
    loginbean_loginid = models.IntegerField(db_column='loginBean_loginId', blank=True, null=True)  # Field name made lowercase.
    redirect_to_new_layout = models.TextField(blank=True, null=True)
    duplicate_restriction = models.BooleanField(blank=True, null=True)
    donation_flag = models.BooleanField(blank=True, null=True)
    round_off = models.BooleanField(blank=True, null=True)
    refund_type = models.TextField(blank=True, null=True)
    risk_category = models.IntegerField(blank=True, null=True)
    ispaybylink = models.SmallIntegerField(db_column='isPaybyLink', blank=True, null=True)  # Field name made lowercase.
    ispaybyform = models.SmallIntegerField(db_column='isPaybyForm', blank=True, null=True)  # Field name made lowercase.
    mesaage_bypass_flag = models.BooleanField(blank=True, null=True)
    van_flag = models.BooleanField(blank=True, null=True)
    tpv_flag = models.BooleanField(blank=True, null=True)
    abort_job_flag = models.BooleanField(blank=True, null=True)
    gift_card_flag = models.BooleanField(blank=True, null=True)
    is_client_logo_flag = models.SmallIntegerField(blank=True, null=True)
    is_commercial_flag = models.SmallIntegerField(blank=True, null=True)
    is_partnerbank_logo_flag = models.SmallIntegerField(blank=True, null=True)
    is_whitelisted = models.BooleanField(blank=True, null=True)
    api_version = models.IntegerField(blank=True, null=True)
    is_vpa_verify = models.BooleanField(blank=True, null=True)
    login_id = models.IntegerField(blank=True, null=True)
    client_mcc = models.CharField(max_length=20, blank=True, null=True)
    client_alert_flag = models.BooleanField(blank=True, null=True)
    client_alert_message = models.CharField(max_length=100, blank=True, null=True)
    force_success_flag = models.BooleanField(blank=True, null=True)
    client_disable_flag = models.BooleanField(blank=True, null=True)
    client_disable_message = models.CharField(max_length=250, blank=True, null=True)
    checkout_cancel_btn = models.SmallIntegerField(blank=True, null=True)
    business_ctg_code = models.CharField(max_length=50, blank=True, null=True)
    referral_code = models.CharField(max_length=50, blank=True, null=True)
    refund_day = models.IntegerField(blank=True, null=True)
    is_unicode_allowed = models.SmallIntegerField(blank=True, null=True)
    operation_type = models.TextField(blank=True, null=True)
    history_timestamp = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'client_data_table_history'


class ClientEpMappingsConfiguration(models.Model):
    mapping_id = models.IntegerField(primary_key=True)
    client_id = models.IntegerField(blank=True, null=True)
    endpoint_id = models.IntegerField(blank=True, null=True)
    paymode_id = models.IntegerField(blank=True, null=True)
    ep_mrchnt_id = models.TextField(blank=True, null=True)
    ep_passwd = models.TextField(blank=True, null=True)
    ep_url = models.TextField(blank=True, null=True)
    ep_user_name = models.TextField(blank=True, null=True)
    fee_forward = models.TextField(blank=True, null=True)
    has_slabs = models.TextField(blank=True, null=True)
    param1 = models.TextField(blank=True, null=True)
    param2 = models.TextField(blank=True, null=True)
    param3 = models.TextField(blank=True, null=True)
    param4 = models.TextField(blank=True, null=True)
    param5 = models.TextField(blank=True, null=True)
    param6 = models.TextField(blank=True, null=True)
    param7 = models.TextField(blank=True, null=True)
    param8 = models.TextField(blank=True, null=True)
    param9 = models.TextField(blank=True, null=True)
    priority = models.IntegerField(blank=True, null=True)
    fee_fee = models.ForeignKey('FeeDataTable', models.DO_NOTHING, blank=True, null=True)
    ep_pass = models.TextField(blank=True, null=True)
    active = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'client_ep_mappings_configuration'


class ClientEpMappingsConfigurationFeeSet(models.Model):
    client_mapping_data_mapping = models.ForeignKey(ClientEpMappingsConfiguration, models.DO_NOTHING)
    fee_set_fee = models.OneToOneField('FeeDataTable', models.DO_NOTHING, primary_key=True)  # The composite primary key (fee_set_fee_id, client_mapping_data_mapping_id) found, that is not supported. The first column is selected.

    class Meta:
        managed = False
        db_table = 'client_ep_mappings_configuration_fee_set'
        unique_together = (('fee_set_fee', 'client_mapping_data_mapping'),)


class ClientEpMappingsConfigurationHistory(models.Model):
    mapping_id = models.IntegerField()
    client_id = models.IntegerField(blank=True, null=True)
    endpoint_id = models.IntegerField(blank=True, null=True)
    paymode_id = models.IntegerField(blank=True, null=True)
    ep_mrchnt_id = models.TextField(blank=True, null=True)
    ep_passwd = models.TextField(blank=True, null=True)
    ep_url = models.TextField(blank=True, null=True)
    ep_user_name = models.TextField(blank=True, null=True)
    fee_forward = models.TextField(blank=True, null=True)
    has_slabs = models.TextField(blank=True, null=True)
    param1 = models.TextField(blank=True, null=True)
    param2 = models.TextField(blank=True, null=True)
    param3 = models.TextField(blank=True, null=True)
    param4 = models.TextField(blank=True, null=True)
    param5 = models.TextField(blank=True, null=True)
    param6 = models.TextField(blank=True, null=True)
    param7 = models.TextField(blank=True, null=True)
    param8 = models.TextField(blank=True, null=True)
    param9 = models.TextField(blank=True, null=True)
    priority = models.IntegerField(blank=True, null=True)
    fee_fee_id = models.IntegerField(blank=True, null=True)
    ep_pass = models.TextField(blank=True, null=True)
    active = models.BooleanField(blank=True, null=True)
    history_timestamp = models.DateTimeField(blank=True, null=True)
    operation_type = models.CharField(max_length=10)

    class Meta:
        managed = False
        db_table = 'client_ep_mappings_configuration_history'


class ClientFeeBearer(models.Model):
    id = models.AutoField()
    client_code = models.CharField(max_length=10, blank=True, null=True)
    trans_date = models.DateField(blank=True, null=True)
    paymode_id = models.CharField(max_length=5, blank=True, null=True)
    fee_bearer_id = models.CharField(max_length=10, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    referral_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'client_fee_bearer'


class ClientPaymentMode(models.Model):
    client_paymode_id = models.IntegerField(primary_key=True)
    paymode_flag = models.BooleanField(blank=True, null=True)
    payment_mode_id = models.IntegerField(blank=True, null=True)
    payment_mode_name = models.TextField(blank=True, null=True)
    client_data_client = models.ForeignKey(ClientDataTable, models.DO_NOTHING, blank=True, null=True)
    is_frm_applicable = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'client_payment_mode'


class ClientPaymentModeHistory(models.Model):
    client_paymode_id = models.IntegerField()
    paymode_flag = models.BooleanField(blank=True, null=True)
    payment_mode_id = models.IntegerField(blank=True, null=True)
    payment_mode_name = models.TextField(blank=True, null=True)
    client_data_client_id = models.IntegerField(blank=True, null=True)
    is_frm_appliable = models.BooleanField(blank=True, null=True)
    is_frm_applicable = models.BooleanField(blank=True, null=True)
    history_timestamp = models.DateTimeField(blank=True, null=True)
    operation_type = models.CharField(max_length=10)

    class Meta:
        managed = False
        db_table = 'client_payment_mode_history'


class ClientPaymodeMapping(models.Model):
    client_payment_mode = models.ForeignKey(ClientPaymentMode, models.DO_NOTHING)
    mapping = models.OneToOneField(ClientEpMappingsConfiguration, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'client_paymode_mapping'


class ClientRequestTempStore(models.Model):
    client_code = models.TextField(primary_key=True)  # The composite primary key (client_code, client_txn_id, txn_ini_date) found, that is not supported. The first column is selected.
    client_txn_id = models.TextField()
    payee_address = models.TextField(blank=True, null=True)
    payee_address1 = models.TextField(blank=True, null=True)
    payee_address2 = models.TextField(blank=True, null=True)
    amount_type = models.TextField(blank=True, null=True)
    app_id = models.TextField(blank=True, null=True)
    application_name = models.TextField(blank=True, null=True)
    bid = models.TextField(blank=True, null=True)
    branch = models.TextField(blank=True, null=True)
    by_pass_option = models.TextField(blank=True, null=True)
    card_holder_name = models.TextField(blank=True, null=True)
    card_number = models.CharField(max_length=50, blank=True, null=True)
    card_type = models.TextField(blank=True, null=True)
    cid = models.TextField(blank=True, null=True)
    client_check_sum = models.TextField(blank=True, null=True)
    client_endpoint = models.TextField(blank=True, null=True)
    client_failed_ru_url = models.TextField(blank=True, null=True)
    client_id = models.TextField(blank=True, null=True)
    client_key = models.TextField(blank=True, null=True)
    client_name = models.TextField(blank=True, null=True)
    client_paymode = models.TextField(blank=True, null=True)
    client_return_url = models.TextField(blank=True, null=True)
    client_app_id = models.TextField(blank=True, null=True)
    conv_charges = models.FloatField(blank=True, null=True)
    ep_charges = models.FloatField(blank=True, null=True)
    email_id = models.TextField(blank=True, null=True)
    end_date = models.TextField(blank=True, null=True)
    end_point_id = models.TextField(blank=True, null=True)
    enrollment_number = models.TextField(blank=True, null=True)
    expiry_date = models.TextField(blank=True, null=True)
    first_name = models.TextField(blank=True, null=True)
    gender = models.TextField(blank=True, null=True)
    gr_number = models.TextField(blank=True, null=True)
    gst = models.FloatField(blank=True, null=True)
    last_name = models.TextField(blank=True, null=True)
    mobile_number = models.TextField(blank=True, null=True)
    paid_amount = models.FloatField(blank=True, null=True)
    partner_id = models.TextField(blank=True, null=True)
    password = models.TextField(blank=True, null=True)
    pay_cycle = models.TextField(blank=True, null=True)
    payee_contact_number = models.TextField(blank=True, null=True)
    payee_email = models.TextField(blank=True, null=True)
    payee_first_name = models.TextField(blank=True, null=True)
    payee_last_name = models.TextField(blank=True, null=True)
    payee_mid_name = models.TextField(blank=True, null=True)
    payment_mode_id = models.TextField(blank=True, null=True)
    profile = models.TextField(blank=True, null=True)
    program_id = models.TextField(blank=True, null=True)
    request_amount = models.TextField(blank=True, null=True)
    semester = models.TextField(blank=True, null=True)
    start_date = models.TextField(blank=True, null=True)
    student_pay_cycle = models.TextField(blank=True, null=True)
    txn_amount = models.FloatField(blank=True, null=True)
    txn_ini_date = models.DateTimeField()
    udf1 = models.TextField(blank=True, null=True)
    udf10 = models.TextField(blank=True, null=True)
    udf2 = models.TextField(blank=True, null=True)
    udf3 = models.TextField(blank=True, null=True)
    udf4 = models.TextField(blank=True, null=True)
    udf5 = models.TextField(blank=True, null=True)
    udf6 = models.TextField(blank=True, null=True)
    udf7 = models.TextField(blank=True, null=True)
    udf8 = models.TextField(blank=True, null=True)
    udf9 = models.TextField(blank=True, null=True)
    user_name = models.TextField(blank=True, null=True)
    udf11 = models.TextField(blank=True, null=True)
    udf12 = models.TextField(blank=True, null=True)
    udf13 = models.TextField(blank=True, null=True)
    udf14 = models.TextField(blank=True, null=True)
    udf15 = models.TextField(blank=True, null=True)
    udf16 = models.TextField(blank=True, null=True)
    udf17 = models.TextField(blank=True, null=True)
    udf18 = models.TextField(blank=True, null=True)
    udf19 = models.TextField(blank=True, null=True)
    udf20 = models.TextField(blank=True, null=True)
    channel_id = models.TextField(blank=True, null=True)
    page_load = models.SmallIntegerField(blank=True, null=True)
    mode_transfer = models.TextField(blank=True, null=True)
    card_exp_month = models.CharField(max_length=10, blank=True, null=True)
    card_exp_year = models.CharField(max_length=10, blank=True, null=True)
    payment_brand = models.TextField(blank=True, null=True)
    challan_no = models.CharField(max_length=100, blank=True, null=True)
    donation_amount = models.FloatField(blank=True, null=True)
    payer_account_number = models.CharField(max_length=50, blank=True, null=True)
    bank_id = models.IntegerField(blank=True, null=True)
    payer_vpa = models.TextField(blank=True, null=True)
    mcc = models.CharField(max_length=20, blank=True, null=True)
    sabpaisa_resp_code = models.CharField(max_length=50, blank=True, null=True)
    sabpaisa_errorcode = models.TextField(blank=True, null=True)
    sabpaisa_message = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    trans_complete_date = models.DateTimeField(blank=True, null=True)
    browser_details = models.TextField(blank=True, null=True)
    merchant_payment_source_url = models.TextField(blank=True, null=True)
    seamless_type = models.CharField(max_length=15, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'client_request_temp_store'
        unique_together = (('client_code', 'client_txn_id', 'txn_ini_date'),)


class ClientZoneCodeMapper(models.Model):
    id = models.IntegerField(primary_key=True)
    client_code = models.CharField(max_length=10, blank=True, null=True)
    zone_code = models.CharField(max_length=10, blank=True, null=True)
    original_zone_code = models.CharField(max_length=20, blank=True, null=True)
    userloginid = models.CharField(db_column='userLoginId', max_length=100, blank=True, null=True)  # Field name made lowercase.
    created_on = models.DateTimeField(blank=True, null=True)
    old_userlogin = models.CharField(db_column='old_userLogin', max_length=75, blank=True, null=True)  # Field name made lowercase.
    zone_head_name = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'client_zone_code_mapper'


class ClientZoneCodeMapperHistory(models.Model):
    id = models.IntegerField()
    client_code = models.CharField(max_length=10, blank=True, null=True)
    zone_code = models.CharField(max_length=10, blank=True, null=True)
    original_zone_code = models.CharField(max_length=20, blank=True, null=True)
    userloginid = models.CharField(db_column='userLoginId', max_length=100, blank=True, null=True)  # Field name made lowercase.
    created_on = models.DateTimeField(blank=True, null=True)
    old_userlogin = models.CharField(db_column='old_userLogin', max_length=75, blank=True, null=True)  # Field name made lowercase.
    zone_head_name = models.CharField(max_length=100, blank=True, null=True)
    history_timestamp = models.DateTimeField(blank=True, null=True)
    operation_type = models.CharField(max_length=10)

    class Meta:
        managed = False
        db_table = 'client_zone_code_mapper_history'


class CompanyInfo(models.Model):
    id = models.BigAutoField()
    designation = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    website = models.CharField(max_length=100, blank=True, null=True)
    company_size = models.BigIntegerField(blank=True, null=True)
    gstin = models.CharField(max_length=100, blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True, null=True)
    address_line_1 = models.CharField(max_length=100, blank=True, null=True)
    address_line_2 = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=20, blank=True, null=True)
    logo_path = models.CharField(max_length=1000, blank=True, null=True)
    company_domain = models.CharField(max_length=100, blank=True, null=True)
    approval_status = models.IntegerField()
    created_on = models.DateTimeField(blank=True, null=True)
    updated_on = models.DateTimeField(blank=True, null=True)
    updated_by = models.CharField(max_length=100, blank=True, null=True)
    user_id = models.BigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'company_info'


class DailyDisbursement(models.Model):
    id = models.IntegerField(primary_key=True)
    date = models.DateField()
    txn_count = models.IntegerField(blank=True, null=True)
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    terminal_status = models.CharField(max_length=50, blank=True, null=True)
    current_status = models.CharField(max_length=50, blank=True, null=True)
    ref_number = models.CharField(max_length=100, blank=True, null=True)
    disbursement_ref_number = models.CharField(max_length=100, blank=True, null=True)
    picked_for_status_check = models.IntegerField(blank=True, null=True)
    file_url = models.TextField(blank=True, null=True)
    created_on = models.DateTimeField(blank=True, null=True)
    updated_on = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'daily_disbursement'


class DailyDisbursementDetail(models.Model):
    daily_disbursement = models.ForeignKey(DailyDisbursement, models.DO_NOTHING)
    client_code = models.CharField(max_length=100)
    txn_id = models.CharField(max_length=100)
    txn_date = models.DateField()
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    mode = models.CharField(max_length=50, blank=True, null=True)
    ref_number = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=100, blank=True, null=True)
    reason = models.TextField(blank=True, null=True)
    disbursement_ref_number = models.CharField(max_length=100, blank=True, null=True)
    is_settled = models.BooleanField(blank=True, null=True)
    created_on = models.DateTimeField(blank=True, null=True)
    modified_on = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'daily_disbursement_detail'


class Domain(models.Model):
    id = models.BigAutoField()
    company_domain = models.CharField(max_length=100, blank=True, null=True)
    status = models.BooleanField(blank=True, null=True)
    company_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'domain'


class DonationTable(models.Model):
    donation_detail_id = models.IntegerField(primary_key=True)
    donation_amount = models.TextField(blank=True, null=True)
    donation_name = models.TextField(blank=True, null=True)
    client_id_client = models.ForeignKey(ClientDataTable, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'donation_table'


class EndpointDataTable(models.Model):
    ep_id = models.IntegerField(primary_key=True)
    account_no = models.TextField(blank=True, null=True)
    agr_name = models.TextField(blank=True, null=True)
    bank_id = models.TextField(blank=True, null=True)
    bank_name = models.TextField(blank=True, null=True)
    ep_contact = models.TextField(blank=True, null=True)
    ep_email = models.TextField(blank=True, null=True)
    ep_mrchnt_id = models.TextField(blank=True, null=True)
    ep_name = models.TextField(blank=True, null=True)
    ep_pass = models.TextField(blank=True, null=True)
    ep_type = models.TextField(blank=True, null=True)
    ep_user_name = models.TextField(blank=True, null=True)
    param1 = models.TextField(blank=True, null=True)
    param2 = models.TextField(blank=True, null=True)
    param3 = models.TextField(blank=True, null=True)
    param4 = models.TextField(blank=True, null=True)
    param5 = models.TextField(blank=True, null=True)
    param6 = models.TextField(blank=True, null=True)
    param7 = models.TextField(blank=True, null=True)
    param8 = models.TextField(blank=True, null=True)
    param9 = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'endpoint_data_table'


class EpResponseTempStore(models.Model):
    temp_id = models.IntegerField(primary_key=True)
    sp_txn_id = models.TextField(blank=True, null=True)
    amount = models.TextField(blank=True, null=True)
    auth_id_code = models.TextField(blank=True, null=True)
    bank_name = models.TextField(blank=True, null=True)
    bank_txn_id = models.TextField(blank=True, null=True)
    challan_number = models.TextField(blank=True, null=True)
    client_txn_id = models.TextField(blank=True, null=True)
    email_id = models.TextField(blank=True, null=True)
    ap_name = models.TextField(blank=True, null=True)
    ep_paymode = models.TextField(blank=True, null=True)
    ep_txn_id = models.TextField(blank=True, null=True)
    mobile_number = models.TextField(blank=True, null=True)
    payer_fname = models.TextField(blank=True, null=True)
    payer_lname = models.TextField(blank=True, null=True)
    resp_date = models.DateTimeField(blank=True, null=True)
    response_code = models.TextField(blank=True, null=True)
    status = models.TextField(blank=True, null=True)
    udf1 = models.TextField(blank=True, null=True)
    udf2 = models.TextField(blank=True, null=True)
    udf3 = models.TextField(blank=True, null=True)
    udf4 = models.TextField(blank=True, null=True)
    udf5 = models.TextField(blank=True, null=True)
    udf86 = models.TextField(blank=True, null=True)
    udf87 = models.TextField(blank=True, null=True)
    udf8 = models.TextField(blank=True, null=True)
    upi = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ep_response_temp_store'


class ExpectedTsrMaster(models.Model):
    id = models.IntegerField(primary_key=True)
    payment_mode_id = models.IntegerField(blank=True, null=True)
    ep_id = models.IntegerField(blank=True, null=True)
    expected_tsr = models.FloatField(blank=True, null=True)
    is_active = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'expected_tsr_master'


class ExportUsername(models.Model):
    id = models.IntegerField(primary_key=True)
    user_name = models.CharField(max_length=100, blank=True, null=True)
    key_value = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'export_username'


class FeeApproved(models.Model):
    approved_id = models.IntegerField(primary_key=True)
    approved_by = models.CharField(max_length=45, blank=True, null=True)
    approved_on = models.DateTimeField(blank=True, null=True)
    client_code = models.CharField(max_length=45, blank=True, null=True)
    approved_for = models.CharField(max_length=50, blank=True, null=True)
    old_values = models.CharField(max_length=55, blank=True, null=True)
    new_values = models.CharField(max_length=55, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'fee_approved'


class FeeBearer(models.Model):
    id = models.AutoField()
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)
    status = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'fee_bearer'


class FeeDataTable(models.Model):
    fee_id = models.IntegerField(primary_key=True)
    convcharges = models.FloatField(blank=True, null=True)
    convcharges_type = models.TextField(blank=True, null=True)
    end_pointcharge = models.FloatField(blank=True, null=True)
    end_pointcharges_types = models.TextField(blank=True, null=True)
    gst = models.FloatField(blank=True, null=True)
    gst_type = models.TextField(blank=True, null=True)
    slab_ceiling = models.FloatField(blank=True, null=True)
    slab_floor = models.FloatField(blank=True, null=True)
    slab_number = models.IntegerField(blank=True, null=True)
    is_tax_applicable_convcharges = models.BooleanField(blank=True, null=True)
    is_tax_applicable_end_pointcharge = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'fee_data_table'


class FormMaster(models.Model):
    form_id = models.IntegerField()
    form_name = models.CharField(max_length=100)
    url = models.CharField(max_length=300)
    parent_id = models.IntegerField()
    sortorder = models.IntegerField(db_column='sortOrder', blank=True, null=True)  # Field name made lowercase.
    sysytem_admin_only = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'form_master'


class HibernateSequence(models.Model):
    next_val = models.BigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'hibernate_sequence'


class ImportBatch(models.Model):
    id = models.BigIntegerField(primary_key=True)
    uploaded_by = models.TextField(blank=True, null=True)
    file = models.CharField(max_length=100, blank=True, null=True)
    file_url = models.CharField(max_length=500, blank=True, null=True)
    update_type = models.CharField(max_length=20)
    uploaded_at = models.DateTimeField()
    file_status = models.CharField(max_length=20)
    processed_at = models.DateTimeField(blank=True, null=True)
    total_rows = models.IntegerField()
    success_count = models.IntegerField()
    failure_count = models.IntegerField()
    failures = models.TextField()  # This field type is a guess.
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'import_batch'


class LoginAttempts(models.Model):
    id = models.AutoField()
    attempts = models.IntegerField(blank=True, null=True)
    user_id = models.IntegerField()
    updated_on = models.DateTimeField(blank=True, null=True)
    updated_by = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'login_attempts'


class Logs(models.Model):
    id = models.AutoField(db_column='Id')  # Field name made lowercase.
    module = models.CharField(max_length=255, blank=True, null=True)
    number_of_transaction = models.CharField(max_length=255, blank=True, null=True)
    successful_transction = models.CharField(max_length=255, blank=True, null=True)
    unsuccessful_transaction = models.CharField(max_length=255, blank=True, null=True)
    user_id = models.IntegerField(blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    company_id = models.IntegerField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    level = models.CharField(max_length=50, blank=True, null=True)
    action = models.CharField(max_length=100, blank=True, null=True)
    log_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'logs'


class LookupCategory(models.Model):
    id = models.IntegerField(primary_key=True)
    category_name = models.TextField(blank=True, null=True)
    category_code = models.CharField(max_length=10, blank=True, null=True)
    is_active = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'lookup_category'


class MerchantBank(models.Model):
    id = models.AutoField()
    email_id = models.CharField(max_length=255, blank=True, null=True)
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    account_holder_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=20)
    bank_name = models.CharField(max_length=255)
    ifsc_code = models.CharField(max_length=15)
    merchant_id = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'merchant_bank'


class MerchantBaseRate(models.Model):
    id = models.AutoField()
    client_code = models.CharField(max_length=50)
    paymodename = models.CharField(max_length=100)
    epname = models.CharField(max_length=100)
    slabnumber = models.CharField(max_length=100)
    slabfloor = models.CharField(max_length=100)
    slabceiling = models.CharField(max_length=100)
    convcharges = models.CharField(max_length=100)
    convchargestype = models.CharField(max_length=100)
    endpointcharge = models.CharField(max_length=100)
    endpointchargestypes = models.CharField(max_length=100)
    gst = models.CharField(max_length=100)
    gsttype = models.CharField(max_length=50)
    mappingid = models.CharField(max_length=100)
    clientid = models.IntegerField()
    endpointid = models.CharField(max_length=100)
    paymodeid = models.IntegerField()
    epmrchntid = models.CharField(max_length=100)
    feesetfeeid = models.CharField(max_length=100)
    feeforward = models.CharField(max_length=11)
    ref_id = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'merchant_base_rate'


class MerchantData(models.Model):
    merchantid = models.CharField(max_length=50)
    name = models.CharField(max_length=255, blank=True, null=True)
    email_id = models.CharField(max_length=255, blank=True, null=True)
    contactnumber = models.BigIntegerField(blank=True, null=True)
    companyname = models.CharField(max_length=255, blank=True, null=True)
    clientname = models.CharField(max_length=255, blank=True, null=True)
    clientcode = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=255, blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    client_id = models.CharField(max_length=50, blank=True, null=True)
    client_type = models.CharField(max_length=255, blank=True, null=True)
    merchant_type_id = models.IntegerField(blank=True, null=True)
    parent_id = models.IntegerField(blank=True, null=True)
    rolling_reserve = models.BooleanField(blank=True, null=True)
    no_of_days = models.IntegerField(blank=True, null=True)
    subscribe = models.BooleanField(blank=True, null=True)
    rolling_percentage = models.FloatField(blank=True, null=True)
    subscribe_amount = models.FloatField(blank=True, null=True)
    pending_subscribe_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    loginmasterid = models.IntegerField(blank=True, null=True)
    business_ctg_id = models.CharField(blank=True, null=True)
    referral_ep_charges_prcnt = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    referral_handling_charges_prcnt = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    sp_ep_charges_prcnt = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    sp_handling_charges_prcnt = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'merchant_data'


class MerchantFeeBearer(models.Model):
    id = models.AutoField()
    merchant_id = models.IntegerField(blank=True, null=True)
    mode_id = models.CharField(max_length=5, blank=True, null=True)
    fee_bearer_id = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'merchant_fee_bearer'


class MerchantType(models.Model):
    id = models.AutoField()
    name = models.CharField(max_length=255)
    code = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'merchant_type'


class MerchantWhitelist(models.Model):
    merchant_whitelist_id = models.IntegerField(primary_key=True)
    active = models.BooleanField(blank=True, null=True)
    white_list = models.TextField(blank=True, null=True)
    client = models.ForeignKey(ClientDataTable, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'merchant_whitelist'


class MerchantWhitelistHistory(models.Model):
    merchant_whitelist_id = models.IntegerField()
    active = models.BooleanField(blank=True, null=True)
    white_list = models.TextField(blank=True, null=True)
    client_id = models.IntegerField()
    history_timestamp = models.DateTimeField(blank=True, null=True)
    operation_type = models.CharField(max_length=10)

    class Meta:
        managed = False
        db_table = 'merchant_whitelist_history'


class Module(models.Model):
    id = models.IntegerField()
    title = models.CharField(max_length=50)
    is_parent = models.BooleanField(blank=True, null=True)
    parent_id = models.IntegerField(blank=True, null=True)
    key = models.CharField(max_length=100, blank=True, null=True)
    path = models.CharField(max_length=100, blank=True, null=True)
    translatekey = models.CharField(max_length=100, blank=True, null=True)
    icon = models.CharField(max_length=100, blank=True, null=True)
    type = models.CharField(max_length=100, blank=True, null=True)
    sort_order = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'module'


class PartnerBank(models.Model):
    partner_bank_id = models.IntegerField(primary_key=True)
    bank_logo_path = models.TextField(blank=True, null=True)
    bank_name = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'partner_bank'


class PaymentMode(models.Model):
    paymode_id = models.BigAutoField(primary_key=True)
    paymode_name = models.CharField(max_length=255, blank=True, null=True)
    paymode_type = models.CharField(max_length=255, blank=True, null=True)
    active = models.CharField(max_length=10, blank=True, null=True)
    code = models.CharField(max_length=5, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'payment_mode'


class PaymentStatusMaster(models.Model):
    id = models.IntegerField(primary_key=True)
    payment_status_code = models.CharField(max_length=45)
    payment_status_name = models.CharField(max_length=45)
    is_active = models.SmallIntegerField(blank=True, null=True)
    created_on = models.DateTimeField(blank=True, null=True)
    created_by = models.CharField(max_length=45, blank=True, null=True)
    modified_on = models.DateTimeField(blank=True, null=True)
    modified_by = models.CharField(max_length=45, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'payment_status_master'


class PaymodeAggregator(models.Model):
    id = models.IntegerField(primary_key=True)
    paymode_id = models.CharField(max_length=45, blank=True, null=True)
    aggregator_code = models.CharField(max_length=45, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'paymode_aggregator'


class PaymodeToEndpointMapping(models.Model):
    paymode = models.OneToOneField(PaymentMode, models.DO_NOTHING, primary_key=True)  # The composite primary key (paymode_id, ep_id) found, that is not supported. The first column is selected.
    ep = models.ForeignKey(EndpointDataTable, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'paymode_to_endpoint_mapping'
        unique_together = (('paymode', 'ep'),)


class Permission(models.Model):
    id = models.IntegerField()
    title = models.CharField(max_length=50)
    moduleid = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'permission'


class PushapiLoggingHistory(models.Model):
    logging_history_id = models.IntegerField(primary_key=True)
    request_time_stamp = models.DateTimeField(blank=True, null=True)
    txn_id = models.CharField(max_length=25, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pushapi_logging_history'


class RateMappingAuth(models.Model):
    login_id = models.IntegerField(unique=True)
    manage_client = models.BooleanField(blank=True, null=True)
    manage_payment_mode = models.BooleanField(blank=True, null=True)
    manage_mapping = models.BooleanField(blank=True, null=True)
    manage_fee = models.BooleanField(blank=True, null=True)
    manage_client_configuration = models.BooleanField(blank=True, null=True)
    manage_feed_forwarded = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'rate_mapping_auth'


class ReconConfigs(models.Model):
    id = models.BigAutoField()
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    transaction_mode = models.CharField(max_length=100, blank=True, null=True)
    transaction_approver = models.CharField(max_length=100, blank=True, null=True)
    transaction_status = models.CharField(max_length=100, blank=True, null=True)
    company_domain = models.CharField(max_length=100, blank=True, null=True)
    created_by = models.CharField(max_length=100, blank=True, null=True)
    created_on = models.DateTimeField(blank=True, null=True)
    updated_by = models.CharField(max_length=100, blank=True, null=True)
    updated_on = models.DateTimeField(blank=True, null=True)
    paid_amount = models.CharField(max_length=100, blank=True, null=True)
    transaction_date_time = models.CharField(max_length=100, blank=True, null=True)
    config_name = models.CharField(max_length=100, blank=True, null=True)
    payee_amount = models.CharField(max_length=50, blank=True, null=True)
    payment_date_time = models.CharField(max_length=50, blank=True, null=True)
    bank_name = models.CharField(max_length=50, blank=True, null=True)
    file_type = models.CharField(max_length=50, blank=True, null=True)
    delimitter = models.CharField(max_length=10, blank=True, null=True)
    is_on_us = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'recon_configs'


class ReconImportLog(models.Model):
    id = models.BigAutoField()
    user_id = models.BigIntegerField(blank=True, null=True)
    processed_record = models.BigIntegerField(blank=True, null=True)
    failed_record = models.BigIntegerField(blank=True, null=True)
    created_on = models.DateTimeField(blank=True, null=True)
    created_by = models.CharField(max_length=100, blank=True, null=True)
    file_path = models.CharField(max_length=100, blank=True, null=True)
    company_domain = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'recon_import_log'


class RefundRequestFromClient(models.Model):
    refund_id = models.IntegerField(primary_key=True)
    amount = models.TextField(blank=True, null=True)
    client_code = models.TextField(blank=True, null=True)
    client_id = models.TextField(blank=True, null=True)
    client_txn_id = models.TextField(blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    refund_complete_date = models.DateTimeField(blank=True, null=True)
    refund_init_date = models.DateTimeField(blank=True, null=True)
    sp_txn_id = models.TextField(blank=True, null=True)
    login_id = models.IntegerField(blank=True, null=True)
    refunded_bank_ref_id = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'refund_request_from_client'


class Revinfo(models.Model):
    rev = models.IntegerField(primary_key=True)
    revtstmp = models.BigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'revinfo'


class RightMaster(models.Model):
    id = models.IntegerField(primary_key=True)
    email_id = models.CharField(max_length=45, blank=True, null=True)
    role_id = models.IntegerField(blank=True, null=True)
    form_id = models.IntegerField(blank=True, null=True)
    is_show = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'right_master'


class Role(models.Model):
    role_id = models.IntegerField(primary_key=True)
    role_name = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'role'


class RolePermission(models.Model):
    roleid = models.IntegerField()
    permissionid = models.IntegerField()
    parent_moduleid = models.IntegerField(blank=True, null=True)
    id = models.AutoField()

    class Meta:
        managed = False
        db_table = 'role_permission'


class RolePrivileges(models.Model):
    id = models.BigAutoField()
    create_rule = models.BooleanField(blank=True, null=True)
    edit_rule = models.BooleanField(blank=True, null=True)
    delete_rule = models.BooleanField(blank=True, null=True)
    create_recon_config = models.BooleanField(blank=True, null=True)
    edit_recon_config = models.BooleanField(blank=True, null=True)
    delete_recon_config = models.BooleanField(blank=True, null=True)
    add_stakeholder = models.BooleanField(blank=True, null=True)
    edit_stakeholder = models.BooleanField(blank=True, null=True)
    delete_stakeholder = models.BooleanField(blank=True, null=True)
    rule_name = models.CharField(max_length=100, blank=True, null=True)
    create_user = models.BooleanField(blank=True, null=True)
    edit_user = models.BooleanField(blank=True, null=True)
    delete_user = models.BooleanField(blank=True, null=True)
    add_admin = models.BooleanField(blank=True, null=True)
    edit_admin = models.BooleanField(blank=True, null=True)
    delete_admin = models.BooleanField(blank=True, null=True)
    company_domain = models.CharField(blank=True, null=True)
    created_by = models.CharField(max_length=6, blank=True, null=True)
    created_on = models.DateTimeField(blank=True, null=True)
    updated_by = models.CharField(max_length=6, blank=True, null=True)
    updated_on = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'role_privileges'


class Roles(models.Model):
    id = models.BigAutoField()
    role_name = models.CharField(max_length=100, blank=True, null=True)
    created_by = models.CharField(max_length=100, blank=True, null=True)
    created_on = models.DateTimeField(blank=True, null=True)
    updated_by = models.CharField(max_length=100, blank=True, null=True)
    updated_on = models.TimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'roles'


class RollingReserveLedger(models.Model):
    id = models.AutoField()
    merchant_settlement_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    rolling_reserve_date = models.DateField(blank=True, null=True)
    percentage = models.IntegerField(blank=True, null=True)
    days_left = models.IntegerField(blank=True, null=True)
    rolling_reserve_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    deductable_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    merchant_payment = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    merchant_settlement_date = models.DateField(blank=True, null=True)
    client_code = models.CharField(max_length=10, blank=True, null=True)
    is_rolling_reserve = models.BooleanField(blank=True, null=True)
    is_subscription = models.BooleanField(blank=True, null=True)
    total_charges = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    pending_subscribe_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    subscribe_paymode_id = models.CharField(max_length=5, blank=True, null=True)
    subscription_ledger_date = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'rolling_reserve_ledger'


class RulesMaster(models.Model):
    id = models.BigAutoField()
    name = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=100)
    created_by = models.CharField(max_length=100, blank=True, null=True)
    updated_by = models.CharField(max_length=100, blank=True, null=True)
    created_on = models.DateTimeField(blank=True, null=True)
    updated_on = models.DateTimeField(blank=True, null=True)
    type = models.CharField(max_length=100, blank=True, null=True)
    company_domain = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_referral = models.BooleanField(blank=True, null=True)
    referral_name = models.CharField(max_length=255, blank=True, null=True)
    referral_id = models.IntegerField(blank=True, null=True)
    client_id = models.CharField(max_length=50, blank=True, null=True)
    service_type = models.CharField(max_length=10, blank=True, null=True)
    stakeholder_detail = models.CharField(max_length=10, blank=True, null=True)
    business_type = models.CharField(max_length=10, blank=True, null=True)
    stakeholder_type = models.IntegerField(blank=True, null=True)
    aggregator_list = models.CharField(max_length=5, blank=True, null=True)
    service_provider_id = models.CharField(max_length=10, blank=True, null=True)
    bank_commission_type = models.CharField(max_length=100, blank=True, null=True)
    bank_commission_value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    is_gst_include = models.IntegerField(blank=True, null=True)
    is_processing_fee = models.IntegerField(blank=True, null=True)
    processing_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    is_on_us = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'rules_master'


class RulesMasterPending(models.Model):
    id = models.BigIntegerField()
    name = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=100)
    created_by = models.CharField(max_length=100, blank=True, null=True)
    updated_by = models.CharField(max_length=100, blank=True, null=True)
    created_on = models.DateTimeField(blank=True, null=True)
    updated_on = models.DateTimeField(blank=True, null=True)
    type = models.CharField(max_length=100, blank=True, null=True)
    company_domain = models.CharField(max_length=100, blank=True, null=True)
    description = models.CharField(max_length=1000, blank=True, null=True)
    mode = models.BigIntegerField(blank=True, null=True)
    business_type = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'rules_master_pending'


class RulesSplitMapping(models.Model):
    id = models.BigAutoField()
    rule_id = models.BigIntegerField(blank=True, null=True)
    split_value = models.FloatField(blank=True, null=True)
    created_on = models.DateTimeField(blank=True, null=True)
    created_by = models.CharField(max_length=100, blank=True, null=True)
    updated_on = models.DateTimeField(blank=True, null=True)
    updated_by = models.CharField(max_length=100, blank=True, null=True)
    stakeholder_id = models.BigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'rules_split_mapping'


class RulesSplitMappingPending(models.Model):
    id = models.BigAutoField()
    rule_id = models.BigIntegerField(blank=True, null=True)
    split_value = models.FloatField(blank=True, null=True)
    created_on = models.DateTimeField(blank=True, null=True)
    created_by = models.CharField(max_length=100, blank=True, null=True)
    updated_on = models.DateTimeField(blank=True, null=True)
    updated_by = models.CharField(max_length=100, blank=True, null=True)
    stakeholder_id = models.BigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'rules_split_mapping_pending'


class ServiceProvider(models.Model):
    id = models.AutoField()
    service_provider_name = models.CharField(max_length=255, blank=True, null=True)
    status = models.BooleanField(blank=True, null=True)
    stakeholder_type_id = models.IntegerField(blank=True, null=True)
    code = models.CharField(max_length=10, blank=True, null=True)
    aggregator_list = models.IntegerField(blank=True, null=True)
    bank_master_id = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'service_provider'


class ServiceType(models.Model):
    id = models.AutoField()
    service_name = models.CharField(max_length=255, blank=True, null=True)
    status = models.BooleanField(blank=True, null=True)
    code = models.CharField(max_length=5, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'service_type'


class ServiceTypeMapper(models.Model):
    id = models.AutoField()
    status = models.BooleanField(blank=True, null=True)
    stakeholder_type_id = models.IntegerField(blank=True, null=True)
    service_type_id = models.CharField(max_length=10, blank=True, null=True)
    aggregator_list = models.CharField(max_length=10, blank=True, null=True)
    service_provider_id = models.CharField(max_length=10, blank=True, null=True)
    bank_master_id = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'service_type_mapper'


class SettledAmtForSubClient(models.Model):
    id = models.IntegerField(primary_key=True)
    client_code = models.CharField(max_length=45, blank=True, null=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    amount_add_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'settled_amt_for_sub_client'


class SettledTransactions(models.Model):
    id = models.BigAutoField()
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    transaction_mode = models.CharField(max_length=100, blank=True, null=True)
    trans_date = models.DateField(blank=True, null=True)
    net_amount = models.FloatField(blank=True, null=True)
    gross_amount = models.FloatField(blank=True, null=True)
    currency = models.CharField(max_length=100, blank=True, null=True)
    conv_fee = models.CharField(max_length=100, blank=True, null=True)
    gst_fee = models.CharField(max_length=100, blank=True, null=True)
    pipe_fee = models.CharField(max_length=100, blank=True, null=True)
    transaction_status = models.CharField(max_length=100, blank=True, null=True)
    payout_status = models.BooleanField(blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(max_length=1000, blank=True, null=True)
    mobile_number = models.CharField(max_length=20, blank=True, null=True)
    created_on = models.DateTimeField(blank=True, null=True)
    created_by = models.CharField(max_length=100, blank=True, null=True)
    company_domain = models.CharField(max_length=100, blank=True, null=True)
    settlement_amount = models.FloatField(blank=True, null=True)
    payment_date = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'settled_transactions'


class SlabMaster(models.Model):
    id = models.BigAutoField()
    slab_max = models.BigIntegerField(blank=True, null=True)
    slab_min = models.IntegerField(blank=True, null=True)
    comission_type = models.CharField(max_length=250, blank=True, null=True)
    comission_value = models.CharField(max_length=250, blank=True, null=True)
    rule_master_id = models.IntegerField(blank=True, null=True)
    handling_charge_type = models.CharField(max_length=20, blank=True, null=True)
    handling_charge = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    alternate_comission_type = models.CharField(max_length=250, blank=True, null=True)
    alternate_comission_value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    comission_condition = models.CharField(max_length=50, blank=True, null=True)
    alternate_handling_charge_type = models.CharField(max_length=20, blank=True, null=True)
    alternate_handling_charge = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    handling_charge_condition = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'slab_master'


class StakeholderType(models.Model):
    id = models.BigAutoField()
    name = models.CharField(max_length=50, blank=True, null=True)
    status = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'stakeholder_type'


class Stakeholders(models.Model):
    id = models.BigAutoField()
    name = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    ifsc_code = models.CharField(max_length=20, blank=True, null=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=20, blank=True, null=True)
    logo = models.CharField(max_length=100, blank=True, null=True)
    stakeholder_type_id = models.BigIntegerField()
    login_access = models.BooleanField(blank=True, null=True)
    password = models.CharField(max_length=1000, blank=True, null=True)
    salt = models.CharField(max_length=1000, blank=True, null=True)
    created_by = models.CharField(max_length=100)
    created_on = models.DateTimeField(blank=True, null=True)
    updated_by = models.CharField(max_length=100, blank=True, null=True)
    updated_on = models.TimeField(blank=True, null=True)
    company_domain = models.CharField(max_length=100, blank=True, null=True)
    stakeholder_id = models.CharField(max_length=100, blank=True, null=True)
    mid = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'stakeholders'


class SubsCommissions(models.Model):
    client_code = models.CharField(max_length=50, blank=True, null=True)
    charges = models.FloatField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)

    class Meta:
        managed = False
        db_table = 'subs_commissions'


class SubscriptionLedger(models.Model):
    id = models.AutoField()
    created_on = models.DateField(blank=True, null=True)
    client_code = models.CharField(max_length=10, blank=True, null=True)
    pending_subscription_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    initial_subscription_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    trans_date = models.DateField(blank=True, null=True)
    type = models.CharField(max_length=20, blank=True, null=True)
    total_charges = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'subscription_ledger'


class TempFeeid1(models.Model):
    fee_id = models.IntegerField(blank=True, null=True)
    status = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'temp_FeeId1'


class TempFeeid2(models.Model):
    fee_id = models.IntegerField(blank=True, null=True)
    status = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'temp_FeeId2'


class TempModeUpdate(models.Model):
    paymodeid = models.IntegerField(blank=True, null=True)
    status = models.BooleanField(blank=True, null=True)
    isexit = models.IntegerField(db_column='isExit', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'temp_Mode_update'


class TempFeesids(models.Model):
    ids = models.IntegerField(primary_key=True)
    feesids = models.IntegerField(blank=True, null=True)
    status = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'temp_feesids'


class TempMapper(models.Model):
    id = models.IntegerField(primary_key=True)
    mapperid = models.IntegerField(blank=True, null=True)
    feesids = models.IntegerField(blank=True, null=True)
    status = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'temp_mapper'


class TempRateCloning(models.Model):
    id = models.IntegerField(primary_key=True)
    mappid = models.CharField(max_length=45, blank=True, null=True)
    status = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'temp_rate_cloning'


class TransPushJobTable(models.Model):
    history_id = models.IntegerField(primary_key=True)
    client_code = models.TextField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    start_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'trans_push_job_table'


class TransactionBank(models.Model):
    id = models.BigAutoField()
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    gross_amount = models.FloatField(blank=True, null=True)
    created_on = models.DateTimeField(blank=True, null=True)
    created_by = models.CharField(max_length=255, blank=True, null=True)
    is_bank_matched = models.BooleanField(blank=True, null=True)
    transaction_status = models.CharField(max_length=255, blank=True, null=True)
    bank_mis_date = models.DateField(blank=True, null=True)
    transaction_mode = models.IntegerField(blank=True, null=True)
    net_amount = models.FloatField(blank=True, null=True)
    payment_date = models.DateField(blank=True, null=True)
    payment_bank = models.CharField(max_length=250, blank=True, null=True)
    trans_date = models.DateTimeField(blank=True, null=True)
    bank_mis_charges = models.FloatField(blank=True, null=True)
    bank_mis_gst = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'transaction_bank'


class TransactionDetail(models.Model):
    txn_id = models.TextField(primary_key=True)  # The composite primary key (txn_id, trans_date) found, that is not supported. The first column is selected.
    act_amount = models.FloatField(blank=True, null=True)
    pg_name = models.TextField(blank=True, null=True)
    pg_pay_mode = models.TextField(blank=True, null=True)
    pg_response_code = models.TextField(blank=True, null=True)
    pg_return_amount = models.FloatField(blank=True, null=True)
    pg_txn_id = models.TextField(blank=True, null=True)
    alert_flag = models.TextField(blank=True, null=True)
    amount_type = models.TextField(blank=True, null=True)
    application_fail_url = models.TextField(blank=True, null=True)
    application_succ_url = models.TextField(blank=True, null=True)
    auth_code = models.TextField(blank=True, null=True)
    bank_txn_id = models.TextField(blank=True, null=True)
    challan_no = models.TextField(blank=True, null=True)
    changed_on_followup = models.TextField(blank=True, null=True)
    client_id = models.IntegerField(blank=True, null=True)
    client_name = models.TextField(blank=True, null=True)
    client_request_ip = models.TextField(blank=True, null=True)
    convcharges = models.FloatField(blank=True, null=True)
    ep_charges = models.FloatField(blank=True, null=True)
    enquiry_counter = models.IntegerField(blank=True, null=True)
    enquiry_date = models.DateTimeField(blank=True, null=True)
    gst = models.FloatField(blank=True, null=True)
    mapping_id = models.IntegerField(blank=True, null=True)
    paid_amount = models.FloatField(blank=True, null=True)
    payee_amount = models.FloatField(blank=True, null=True)
    payee_email = models.TextField(blank=True, null=True)
    payee_first_name = models.TextField(blank=True, null=True)
    payee_lst_name = models.TextField(blank=True, null=True)
    payee_mid_name = models.TextField(blank=True, null=True)
    payee_mob = models.TextField(blank=True, null=True)
    payment_mode = models.TextField(blank=True, null=True)
    program_id = models.TextField(blank=True, null=True)
    refund_date = models.TextField(blank=True, null=True)
    refund_message = models.TextField(blank=True, null=True)
    refund_status_code = models.TextField(blank=True, null=True)
    reg_number = models.TextField(blank=True, null=True)
    resp_msg = models.TextField(blank=True, null=True)
    sabpaisa_resp_code = models.TextField(blank=True, null=True)
    status = models.TextField(blank=True, null=True)
    trans_complete_date = models.DateTimeField(blank=True, null=True)
    trans_date = models.DateTimeField()
    client_code = models.TextField(blank=True, null=True)
    client_txn_id = models.TextField(blank=True, null=True)
    uit_application_id = models.TextField(blank=True, null=True)
    vpa = models.TextField(blank=True, null=True)
    vpa_remarks = models.TextField(blank=True, null=True)
    is_settled = models.BooleanField(blank=True, null=True)
    pag_response_code = models.TextField(blank=True, null=True)
    charge_back_amount = models.FloatField(blank=True, null=True)
    charge_back_date = models.DateTimeField(blank=True, null=True)
    charge_back_status = models.TextField(blank=True, null=True)
    settlement_date = models.DateTimeField(blank=True, null=True)
    settlement_amount = models.FloatField(blank=True, null=True)
    channel_id = models.TextField(blank=True, null=True)
    banktxnid = models.TextField(db_column='bankTxnId', blank=True, null=True)  # Field name made lowercase.
    broser_name = models.TextField(blank=True, null=True)
    trans_push_date = models.DateTimeField(blank=True, null=True)
    trans_flag = models.BooleanField(blank=True, null=True)
    udf20 = models.TextField(blank=True, null=True)
    donation_amount = models.FloatField(blank=True, null=True)
    card_brand = models.TextField(blank=True, null=True)
    device_name = models.CharField(max_length=10, blank=True, null=True)
    bank_message = models.CharField(max_length=300, blank=True, null=True)
    fee_forward = models.CharField(max_length=5, blank=True, null=True)
    payer_confirmation = models.BooleanField(blank=True, null=True)
    refunded_date = models.DateTimeField(blank=True, null=True)
    settlement_status = models.CharField(max_length=100, blank=True, null=True)
    settlement_by = models.CharField(max_length=150, blank=True, null=True)
    settlement_bank_ref = models.CharField(max_length=150, blank=True, null=True)
    settlement_remarks = models.CharField(max_length=150, blank=True, null=True)
    settlement_utr = models.CharField(max_length=150, blank=True, null=True)
    sent_notification_payer_confirmation_dt = models.DateTimeField(blank=True, null=True)
    sent_notification_payer_confirmation_url = models.CharField(max_length=500, blank=True, null=True)
    payer_confirmation_respones = models.CharField(max_length=50, blank=True, null=True)
    payer_confirmation_respones_dt = models.DateTimeField(blank=True, null=True)
    payer_confirmation_request_ct = models.IntegerField(blank=True, null=True)
    refund_request_from = models.CharField(max_length=150, blank=True, null=True)
    chargeback_request_from = models.CharField(max_length=150, blank=True, null=True)
    gst_rate_type = models.CharField(max_length=10, blank=True, null=True)
    udf19 = models.TextField(blank=True, null=True)
    ep_conv_rate = models.FloatField(blank=True, null=True)
    gst_rate = models.FloatField(blank=True, null=True)
    sp_conv_rate = models.FloatField(blank=True, null=True)
    ep_conv_rate_type = models.CharField(max_length=10, blank=True, null=True)
    sp_conv_rate_type = models.CharField(max_length=10, blank=True, null=True)
    bank_errorcode = models.TextField(blank=True, null=True)
    sabpaisa_errorcode = models.TextField(blank=True, null=True)
    settlement_bank_amount = models.FloatField(blank=True, null=True)
    settlement_bank_amount_date = models.DateTimeField(blank=True, null=True)
    terminal_status = models.CharField(max_length=50, blank=True, null=True)
    is_charge_back = models.BooleanField(blank=True, null=True)
    charge_back_debit_amount = models.FloatField(blank=True, null=True)
    charge_back_credit_date_to_merchant = models.DateTimeField(blank=True, null=True)
    charge_back_remarks = models.CharField(max_length=200, blank=True, null=True)
    bank_name = models.CharField(max_length=50, blank=True, null=True)
    amount_available_to_adjust = models.CharField(max_length=50, blank=True, null=True)
    amount_adjust_on = models.DateTimeField(blank=True, null=True)
    money_asked_from_merchant = models.CharField(max_length=50, blank=True, null=True)
    refund_initiated_on = models.DateTimeField(blank=True, null=True)
    refund_process_on = models.DateTimeField(blank=True, null=True)
    refund_reason = models.CharField(max_length=200, blank=True, null=True)
    refunded_amount = models.FloatField(blank=True, null=True)
    refund_track_id = models.CharField(max_length=50, blank=True, null=True)
    arn = models.CharField(max_length=50, blank=True, null=True)
    bank_cb_fee = models.FloatField(blank=True, null=True)
    merchant_cb_status = models.CharField(max_length=20, blank=True, null=True)
    prearb_date = models.DateTimeField(blank=True, null=True)
    cb_credit_date_txn_reject = models.DateTimeField(blank=True, null=True)
    force_success_flag = models.BooleanField(blank=True, null=True)
    bin_update_flag = models.BooleanField(blank=True, null=True)
    conv_gst = models.FloatField(blank=True, null=True)
    endpoint_gst = models.FloatField(blank=True, null=True)
    payment_mode_id = models.IntegerField(blank=True, null=True)
    endpoint_id = models.IntegerField(blank=True, null=True)
    browser_details = models.TextField(blank=True, null=True)
    business_ctg_code = models.CharField(max_length=50, blank=True, null=True)
    referral_code = models.CharField(max_length=50, blank=True, null=True)
    trans_updated_by = models.CharField(max_length=100, blank=True, null=True)
    trans_push_flag = models.BooleanField(blank=True, null=True)
    treasury_bank_scroll_id = models.CharField(max_length=100, blank=True, null=True)
    rolling_reserve_plus = models.FloatField(blank=True, null=True)
    rolling_reserve_minus = models.FloatField(blank=True, null=True)
    effective_settlement_amount = models.FloatField(blank=True, null=True)
    refund_amount = models.FloatField(blank=True, null=True)
    transaction_tracker_id = models.IntegerField(blank=True, null=True)
    transaction_tracker_time = models.DateTimeField(blank=True, null=True)
    settlepaisa_data = models.BooleanField(blank=True, null=True)
    mandate_flag = models.BooleanField(blank=True, null=True)
    mandate_charges = models.FloatField(blank=True, null=True)
    mandate_status = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'transaction_detail'
        unique_together = (('txn_id', 'trans_date'), ('client_code', 'client_txn_id', 'trans_date'),)


class TransactionImportLog(models.Model):
    id = models.BigAutoField()
    user_id = models.BigIntegerField(blank=True, null=True)
    processed_record = models.BigIntegerField(blank=True, null=True)
    failed_record = models.BigIntegerField(blank=True, null=True)
    created_on = models.DateTimeField(blank=True, null=True)
    created_by = models.CharField(max_length=100, blank=True, null=True)
    file_path = models.CharField(max_length=1000, blank=True, null=True)
    company_domain = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'transaction_import_log'


class TransactionModeMaster(models.Model):
    id = models.BigAutoField()
    mode_name = models.CharField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'transaction_mode_master'


class TransactionReconTable(models.Model):
    id = models.BigAutoField()
    transaction_id = models.CharField(blank=True, null=True)
    gross_amount = models.FloatField(blank=True, null=True)
    recon_date = models.DateField(blank=True, null=True)
    transaction_approver = models.CharField(max_length=100, blank=True, null=True)
    created_by = models.CharField(max_length=100, blank=True, null=True)
    created_on = models.DateTimeField(blank=True, null=True)
    transaction_status = models.CharField(max_length=100, blank=True, null=True)
    company_domain = models.CharField(max_length=100, blank=True, null=True)
    is_recon_matched = models.BooleanField(blank=True, null=True)
    transaction_mode = models.IntegerField(blank=True, null=True)
    net_amount = models.FloatField(blank=True, null=True)
    payment_date = models.DateTimeField(blank=True, null=True)
    payment_bank = models.CharField(max_length=250, blank=True, null=True)
    trans_date = models.DateTimeField(blank=True, null=True)
    paid_amount = models.FloatField(blank=True, null=True)
    payee_amount = models.FloatField(blank=True, null=True)
    is_on_us = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'transaction_recon_table'


class TransactionReconTableImportLog(models.Model):
    id = models.BigAutoField()
    user_id = models.BigIntegerField(blank=True, null=True)
    processed_record = models.BigIntegerField(blank=True, null=True)
    failed_record = models.BigIntegerField(blank=True, null=True)
    created_on = models.DateTimeField(blank=True, null=True)
    created_by = models.CharField(max_length=100, blank=True, null=True)
    file_path = models.CharField(max_length=1000, blank=True, null=True)
    company_domain = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'transaction_recon_table_import_log'


class TransactionsToSettle(models.Model):
    id = models.BigAutoField()
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    pg_name = models.CharField(max_length=100, blank=True, null=True)
    pg_pay_mode = models.CharField(max_length=100, blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    act_amount = models.FloatField(blank=True, null=True)
    client_code = models.CharField(max_length=100, blank=True, null=True)
    payee_name = models.CharField(max_length=255, blank=True, null=True)
    payee_email = models.CharField(max_length=1000, blank=True, null=True)
    payee_mobile = models.CharField(max_length=50, blank=True, null=True)
    payee_amount = models.FloatField(blank=True, null=True)
    paid_amount = models.FloatField(blank=True, null=True)
    payment_mode = models.CharField(max_length=20, blank=True, null=True)
    transaction_mode = models.CharField(max_length=100, blank=True, null=True)
    currency = models.CharField(max_length=100, blank=True, null=True)
    convcharges = models.FloatField(blank=True, null=True)
    ep_charges = models.FloatField(blank=True, null=True)
    gst = models.FloatField(blank=True, null=True)
    gst_rate_type = models.CharField(max_length=20, blank=True, null=True)
    gst_rate = models.FloatField(blank=True, null=True)
    conv_gst = models.FloatField(blank=True, null=True)
    endpoint_gst = models.FloatField(blank=True, null=True)
    pipe_fee = models.CharField(max_length=100, blank=True, null=True)
    transaction_status = models.CharField(max_length=100, blank=True, null=True)
    trans_date = models.DateTimeField(blank=True, null=True)
    trans_complete_date = models.DateTimeField(blank=True, null=True)
    payout_status = models.CharField(max_length=250, blank=True, null=True)
    fee_forward = models.CharField(max_length=10, blank=True, null=True)
    sp_conv_rate = models.FloatField(blank=True, null=True)
    sp_conv_rate_type = models.CharField(max_length=30, blank=True, null=True)
    ep_conv_rate = models.FloatField(blank=True, null=True)
    ep_conv_rate_type = models.CharField(max_length=30, blank=True, null=True)
    created_on = models.DateTimeField(blank=True, null=True)
    created_by = models.CharField(max_length=100, blank=True, null=True)
    is_settled = models.CharField(max_length=10, blank=True, null=True)
    settlement_date = models.DateTimeField(blank=True, null=True)
    settlement_amount = models.FloatField(blank=True, null=True)
    settlement_status = models.CharField(max_length=100, blank=True, null=True)
    settlement_by = models.CharField(max_length=100, blank=True, null=True)
    settlement_bank_ref = models.CharField(max_length=100, blank=True, null=True)
    settlement_remarks = models.CharField(max_length=100, blank=True, null=True)
    settlement_utr = models.CharField(max_length=100, blank=True, null=True)
    settlement_bank_amount = models.FloatField(blank=True, null=True)
    settlement_bank_amount_date = models.DateTimeField(blank=True, null=True)
    conv_fee_bearer = models.FloatField(blank=True, null=True)
    is_recon = models.CharField(max_length=10, blank=True, null=True)
    recon_date = models.DateTimeField(blank=True, null=True)
    is_bank_settled = models.CharField(max_length=10, blank=True, null=True)
    is_merchant_settled = models.CharField(max_length=10, blank=True, null=True)
    payment_mode_0 = models.IntegerField(db_column='Payment_mode', blank=True, null=True)  # Field name made lowercase. Field renamed because of name conflict.
    service_provider_id = models.IntegerField(blank=True, null=True)
    referral_code = models.CharField(max_length=128, blank=True, null=True)
    business_category = models.CharField(max_length=128, blank=True, null=True)
    bank_settlement_amount = models.FloatField(blank=True, null=True)
    bank_settled_date = models.DateTimeField(blank=True, null=True)
    merchant_settled_date = models.DateTimeField(blank=True, null=True)
    bank_settle_with_gst_amount = models.FloatField(blank=True, null=True)
    referral_with_gst_amount = models.FloatField(blank=True, null=True)
    bank_settle_gst_amount = models.FloatField(blank=True, null=True)
    referral_amount = models.FloatField(blank=True, null=True)
    referral_gst_amount = models.FloatField(blank=True, null=True)
    bank_exclude_amount = models.FloatField(blank=True, null=True)
    partner = models.CharField(max_length=255, blank=True, null=True)
    referral_name = models.CharField(max_length=255, blank=True, null=True)
    final_distribution_amount = models.FloatField(blank=True, null=True)
    is_bank_matched = models.CharField(max_length=255, blank=True, null=True)
    bank_match_date = models.DateTimeField(blank=True, null=True)
    settled_amount_by_bank = models.FloatField(blank=True, null=True)
    is_referral_settled = models.CharField(max_length=255, blank=True, null=True)
    is_referral_settled_date = models.DateTimeField(blank=True, null=True)
    referral_id = models.IntegerField(blank=True, null=True)
    paymode_id = models.IntegerField(blank=True, null=True)
    payout_date = models.DateTimeField(blank=True, null=True)
    udf1 = models.TextField(blank=True, null=True)
    udf2 = models.TextField(blank=True, null=True)
    udf3 = models.TextField(blank=True, null=True)
    udf4 = models.TextField(blank=True, null=True)
    udf5 = models.TextField(blank=True, null=True)
    udf6 = models.TextField(blank=True, null=True)
    udf7 = models.TextField(blank=True, null=True)
    udf8 = models.TextField(blank=True, null=True)
    udf9 = models.TextField(blank=True, null=True)
    udf10 = models.TextField(blank=True, null=True)
    udf11 = models.TextField(blank=True, null=True)
    udf12 = models.TextField(blank=True, null=True)
    udf13 = models.TextField(blank=True, null=True)
    udf14 = models.TextField(blank=True, null=True)
    udf15 = models.TextField(blank=True, null=True)
    udf16 = models.TextField(blank=True, null=True)
    udf17 = models.TextField(blank=True, null=True)
    udf18 = models.TextField(blank=True, null=True)
    udf19 = models.TextField(blank=True, null=True)
    udf20 = models.TextField(blank=True, null=True)
    client_name = models.CharField(max_length=250, blank=True, null=True)
    client_txn_id = models.CharField(max_length=250, blank=True, null=True)
    challan_no = models.CharField(max_length=250, blank=True, null=True)
    bank_txn_id = models.CharField(max_length=250, blank=True, null=True)
    gr_number = models.CharField(max_length=250, blank=True, null=True)
    payee_address = models.CharField(max_length=250, blank=True, null=True)
    p_gst = models.FloatField(blank=True, null=True)
    p_ep_charges = models.FloatField(blank=True, null=True)
    p_convcharges = models.FloatField(blank=True, null=True)
    pg_return_amount = models.FloatField(blank=True, null=True)
    bank_rule_id = models.IntegerField(blank=True, null=True)
    refferal_rule_id = models.IntegerField(blank=True, null=True)
    rolling_reserve_settlement_date = models.DateField(blank=True, null=True)
    is_rolling_reserve = models.BooleanField(blank=True, null=True)
    rolling_reserve_settled = models.BooleanField(blank=True, null=True)
    rolling_reserve_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    is_fee_bearer = models.CharField(max_length=5, blank=True, null=True)
    pg_charge = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    rolling_deductable_amount = models.DecimalField(max_digits=10, decimal_places=2)
    subscription_charges = models.DecimalField(max_digits=10, decimal_places=2)
    is_fee_bearer_calculate = models.CharField(max_length=5, blank=True, null=True)
    is_rolling_calculate = models.CharField(max_length=5, blank=True, null=True)
    is_payout_done = models.CharField(max_length=5, blank=True, null=True)
    refund_transaction_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    refund_transaction_date = models.DateTimeField(blank=True, null=True)
    is_refund_done = models.CharField(max_length=5, blank=True, null=True)
    refund_type = models.CharField(max_length=50, blank=True, null=True)
    refund_completed_date = models.DateTimeField(blank=True, null=True)
    bank_conv_charge = models.FloatField(blank=True, null=True)
    bank_ep_charge = models.FloatField(blank=True, null=True)
    referral_conv_charge = models.FloatField(blank=True, null=True)
    referral_ep_charge = models.FloatField(blank=True, null=True)
    sabpaisa_ep_share_from_referral = models.FloatField(blank=True, null=True)
    sabpaisa_share = models.FloatField(blank=True, null=True)
    sabpaisa_conv_share_from_referral = models.FloatField(blank=True, null=True)
    sabpaisa_total_share = models.FloatField(blank=True, null=True)
    subscription_ledger_id = models.IntegerField(blank=True, null=True)
    bank_commission_share_type = models.CharField(max_length=100, blank=True, null=True)
    bank_commission_share = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    bank_commission_gst = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    sp_commission_share = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    merchant_unsettling_reason = models.CharField(max_length=500, blank=True, null=True)
    stakeholder_unsettling_reason = models.CharField(max_length=500, blank=True, null=True)
    referral_unsettling_reason = models.CharField(max_length=500, blank=True, null=True)
    is_on_us = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'transactions_to_settle'


class TxnReportS3Detail(models.Model):
    id = models.IntegerField(primary_key=True)
    from_date = models.DateTimeField(blank=True, null=True)
    to_date = models.DateTimeField(blank=True, null=True)
    created_by = models.TextField(blank=True, null=True)
    created_on = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(blank=True, null=True)
    s3_bucket_url = models.CharField(max_length=1000, blank=True, null=True)
    file_gen_status = models.CharField(max_length=45, blank=True, null=True)
    source = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'txn_report_s3_detail'


class UpdatefileReceivedBank(models.Model):
    id = models.IntegerField()
    stackholder_id = models.SmallIntegerField(blank=True, null=True)
    file_path = models.CharField(blank=True, null=True)
    is_recon = models.BooleanField(blank=True, null=True)
    is_recon_date = models.DateField(blank=True, null=True)
    is_bank_settled = models.BooleanField(blank=True, null=True)
    is_bank_settled_date = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'updatefile_received_bank'


class UpiAppDetails(models.Model):
    upi_apps_details_id = models.IntegerField(primary_key=True)
    active = models.BooleanField(blank=True, null=True)
    app_code = models.CharField(unique=True, max_length=10, blank=True, null=True)
    app_name = models.CharField(max_length=100, blank=True, null=True)
    app_url = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'upi_app_details'


class UploadedFile(models.Model):
    id = models.IntegerField()
    name = models.CharField(max_length=255, blank=True, null=True)
    url = models.TextField(blank=True, null=True)
    is_recon = models.BooleanField(blank=True, null=True)
    is_bank = models.BooleanField(blank=True, null=True)
    date = models.DateTimeField(blank=True, null=True)
    other = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'uploaded_file'


class UserZoneMapper(models.Model):
    id = models.IntegerField(primary_key=True)
    emp_email = models.CharField(max_length=150, blank=True, null=True)
    zone_code = models.CharField(max_length=10, blank=True, null=True)
    emp_code = models.CharField(max_length=20, blank=True, null=True)
    mgr_code = models.CharField(max_length=20, blank=True, null=True)
    role_id = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'user_zone_mapper'


class Users(models.Model):
    id = models.BigAutoField()
    first_name = models.CharField(max_length=128, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    phone_country_code = models.CharField(max_length=5, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    password = models.CharField(max_length=1000, blank=True, null=True)
    salt = models.CharField(max_length=1000, blank=True, null=True)
    created_on = models.DateField(blank=True, null=True)
    last_updated_on = models.DateField(blank=True, null=True)
    updated_by = models.CharField(max_length=100, blank=True, null=True)
    deleted_on = models.DateField(blank=True, null=True)
    deleted_by = models.CharField(max_length=100, blank=True, null=True)
    role_id = models.IntegerField(blank=True, null=True)
    approval_status = models.CharField(max_length=20)
    company_id = models.BigIntegerField(blank=True, null=True)
    rec_status = models.BooleanField(blank=True, null=True)
    verification_token = models.CharField(max_length=1000, blank=True, null=True)
    onboarding_completed = models.BooleanField(blank=True, null=True)
    module_role = models.IntegerField(blank=True, null=True)
    manager_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'users'
