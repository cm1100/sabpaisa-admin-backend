"""
Settlement Serializers
Following DRF best practices with proper validation
"""
from rest_framework import serializers
from decimal import Decimal
from .models import (
    SettlementBatch,
    SettlementDetail,
    SettlementReport,
    SettlementConfiguration,
    SettlementReconciliation
)


class SettlementDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for settlement details
    """
    class Meta:
        model = SettlementDetail
        fields = [
            'settlement_id', 'batch', 'txn_id', 'client_code',
            'transaction_amount', 'settlement_amount', 'processing_fee',
            'gst_amount', 'net_amount', 'settlement_date',
            'settlement_status', 'bank_reference', 'utr_number',
            'remarks', 'created_at'
        ]
        read_only_fields = ['settlement_id', 'created_at', 'net_amount']


class SettlementBatchSerializer(serializers.ModelSerializer):
    """
    Serializer for settlement batch
    """
    settlements_count = serializers.IntegerField(source='settlements.count', read_only=True)
    processed_by_username = serializers.CharField(source='processed_by.username', read_only=True)
    
    class Meta:
        model = SettlementBatch
        fields = [
            'batch_id', 'batch_date', 'total_transactions',
            'total_amount', 'processing_fee', 'gst_amount',
            'net_settlement_amount', 'status', 'created_at',
            'processed_at', 'processed_by', 'processed_by_username',
            'settlements_count'
        ]
        read_only_fields = [
            'batch_id', 'created_at', 'net_settlement_amount',
            'settlements_count'
        ]


class CreateSettlementBatchSerializer(serializers.Serializer):
    """
    Serializer for creating settlement batch
    """
    batch_date = serializers.DateField(required=False)
    
    def validate_batch_date(self, value):
        """Validate batch date is not in future"""
        from django.utils import timezone
        if value and value > timezone.now().date():
            raise serializers.ValidationError("Batch date cannot be in future")
        return value


class ProcessSettlementSerializer(serializers.Serializer):
    """
    Serializer for processing settlement
    """
    batch_id = serializers.UUIDField(required=True)
    action = serializers.ChoiceField(
        choices=['APPROVE', 'PROCESS', 'CANCEL'],
        required=True
    )
    remarks = serializers.CharField(required=False, max_length=500)


class SettlementReportSerializer(serializers.ModelSerializer):
    """
    Serializer for settlement reports
    """
    batch_date = serializers.DateField(source='batch.batch_date', read_only=True)
    generated_by_username = serializers.CharField(source='generated_by.username', read_only=True)
    
    class Meta:
        model = SettlementReport
        fields = [
            'report_id', 'batch', 'batch_date', 'report_type',
            'report_date', 'file_path', 'generated_by',
            'generated_by_username', 'generated_at'
        ]
        read_only_fields = ['report_id', 'generated_at']


class GenerateReportSerializer(serializers.Serializer):
    """
    Serializer for generating reports
    """
    batch_id = serializers.UUIDField(required=True)
    report_type = serializers.ChoiceField(
        choices=['DAILY', 'WEEKLY', 'MONTHLY', 'RECONCILIATION', 'SUMMARY'],
        required=True
    )


class SettlementConfigurationSerializer(serializers.ModelSerializer):
    """
    Serializer for settlement configuration
    """
    class Meta:
        model = SettlementConfiguration
        fields = [
            'config_id', 'client_code', 'settlement_cycle',
            'min_settlement_amount', 'processing_fee_percentage',
            'gst_percentage', 'auto_settle', 'bank_account_number',
            'bank_name', 'ifsc_code', 'account_holder_name',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['config_id', 'created_at', 'updated_at']
    
    def validate_processing_fee_percentage(self, value):
        """Validate processing fee percentage"""
        if value < 0 or value > 10:
            raise serializers.ValidationError("Processing fee must be between 0 and 10%")
        return value
    
    def validate_gst_percentage(self, value):
        """Validate GST percentage"""
        if value < 0 or value > 30:
            raise serializers.ValidationError("GST must be between 0 and 30%")
        return value


class SettlementReconciliationSerializer(serializers.ModelSerializer):
    """
    Serializer for settlement reconciliation
    """
    batch_date = serializers.DateField(source='batch.batch_date', read_only=True)
    reconciled_by_username = serializers.CharField(source='reconciled_by.username', read_only=True)
    
    class Meta:
        model = SettlementReconciliation
        fields = [
            'reconciliation_id', 'batch', 'batch_date',
            'bank_statement_amount', 'system_amount',
            'difference_amount', 'reconciliation_status',
            'reconciled_by', 'reconciled_by_username',
            'reconciled_at', 'remarks', 'created_at'
        ]
        read_only_fields = [
            'reconciliation_id', 'created_at', 'difference_amount'
        ]


class CreateReconciliationSerializer(serializers.Serializer):
    """
    Serializer for creating reconciliation
    """
    batch_id = serializers.UUIDField(required=True)
    bank_statement_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=True
    )
    remarks = serializers.CharField(required=False, max_length=1000)
    
    def validate_bank_statement_amount(self, value):
        """Validate bank amount is positive"""
        if value <= 0:
            raise serializers.ValidationError("Bank statement amount must be positive")
        return value


class UpdateReconciliationSerializer(serializers.Serializer):
    """
    Serializer for updating reconciliation status
    """
    status = serializers.ChoiceField(
        choices=['MATCHED', 'MISMATCHED', 'INVESTIGATING', 'RESOLVED'],
        required=True
    )
    remarks = serializers.CharField(required=False, max_length=1000)


class SettlementStatisticsSerializer(serializers.Serializer):
    """
    Serializer for settlement statistics
    """
    total_batches = serializers.IntegerField()
    total_amount_settled = serializers.FloatField()
    total_fees_collected = serializers.FloatField()
    total_gst_collected = serializers.FloatField()
    average_batch_amount = serializers.FloatField()
    completed_batches = serializers.IntegerField()
    pending_batches = serializers.IntegerField()
    success_rate = serializers.FloatField()
    date_range = serializers.CharField()


class ClientSettlementSummarySerializer(serializers.Serializer):
    """
    Serializer for client settlement summary
    """
    client_code = serializers.CharField()
    total_transactions = serializers.IntegerField()
    total_settled_amount = serializers.FloatField()
    total_fees_paid = serializers.FloatField()
    total_gst_paid = serializers.FloatField()
    settled_count = serializers.IntegerField()
    pending_count = serializers.IntegerField()
    settlement_cycle = serializers.CharField()
    auto_settle = serializers.BooleanField()


class SettlementFilterSerializer(serializers.Serializer):
    """
    Serializer for settlement filters
    """
    status = serializers.ChoiceField(
        choices=['PENDING', 'PROCESSING', 'APPROVED', 'COMPLETED', 'FAILED', 'CANCELLED'],
        required=False
    )
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    client_code = serializers.CharField(required=False)
    page = serializers.IntegerField(default=1, min_value=1)
    page_size = serializers.IntegerField(default=20, min_value=1, max_value=100)