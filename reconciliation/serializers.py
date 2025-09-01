from rest_framework import serializers
from .models import (
    TransactionReconTable, BankStatementUpload,
    BankStatementEntry, ReconciliationMismatch,
    ReconciliationRule
)

class ReconciliationStatusSerializer(serializers.Serializer):
    total_transactions = serializers.IntegerField()
    matched = serializers.IntegerField()
    mismatched = serializers.IntegerField()
    pending = serializers.IntegerField()
    match_rate = serializers.FloatField()
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    matched_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    mismatched_amount = serializers.DecimalField(max_digits=15, decimal_places=2)

class TransactionReconSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionReconTable
        fields = '__all__'

class BankStatementUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankStatementUpload
        fields = '__all__'
        read_only_fields = ['upload_id', 'uploaded_at', 'total_records', 
                           'matched_records', 'mismatched_records']

class BankStatementEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = BankStatementEntry
        fields = '__all__'

class ReconciliationMismatchSerializer(serializers.ModelSerializer):
    bank_entry = BankStatementEntrySerializer(source='bank_entry_id', read_only=True)
    
    class Meta:
        model = ReconciliationMismatch
        fields = '__all__'

class ReconciliationRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReconciliationRule
        fields = '__all__'

class ManualMatchSerializer(serializers.Serializer):
    txn_id = serializers.CharField()
    bank_entry_id = serializers.IntegerField()
    remarks = serializers.CharField(required=False)

class ReconciliationReportSerializer(serializers.Serializer):
    date = serializers.DateField()
    total_transactions = serializers.IntegerField()
    matched_count = serializers.IntegerField()
    matched_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    mismatched_count = serializers.IntegerField()
    mismatched_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    match_percentage = serializers.FloatField()

class BankStatementParseSerializer(serializers.Serializer):
    file = serializers.FileField()
    bank_name = serializers.CharField()
    statement_date = serializers.DateField()
    format = serializers.ChoiceField(choices=['CSV', 'EXCEL', 'PDF'])