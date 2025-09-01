from rest_framework import serializers
from .models import (
    RefundRequestFromClient, RefundApprovalWorkflow,
    RefundConfiguration, RefundBatch, RefundBatchItem,
    RefundSettlementAdjustment, TransactionDetail
)
from decimal import Decimal

class RefundRequestSerializer(serializers.ModelSerializer):
    transaction_details = serializers.SerializerMethodField()
    status = serializers.CharField(read_only=True)
    refund_type = serializers.CharField(read_only=True)
    requested_by = serializers.CharField(read_only=True)
    refund_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = RefundRequestFromClient
        fields = '__all__'
        read_only_fields = ['refund_id', 'refund_complete_date']
    
    def get_transaction_details(self, obj):
        try:
            txn = TransactionDetail.objects.get(txn_id=obj.sp_txn_id)
            return {
                'client_name': txn.client_name,
                'paid_amount': float(txn.paid_amount),
                'status': txn.status,
                'is_settled': txn.is_settled
            }
        except:
            return None
    
    def get_refund_amount(self, obj):
        try:
            return float(obj.amount) if obj.amount else 0
        except:
            return 0

class RefundApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefundApprovalWorkflow
        fields = '__all__'

class RefundConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefundConfiguration
        fields = '__all__'

class RefundBatchSerializer(serializers.ModelSerializer):
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = RefundBatch
        fields = '__all__'
        read_only_fields = ['batch_id', 'created_at', 'batch_reference']
    
    def get_items_count(self, obj):
        return RefundBatchItem.objects.filter(batch=obj).count()

class CreateRefundSerializer(serializers.Serializer):
    txn_id = serializers.CharField()
    refund_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    refund_reason = serializers.CharField()
    refund_type = serializers.ChoiceField(choices=['FULL', 'PARTIAL'])
    customer_notified = serializers.BooleanField(default=False)
    
    def validate(self, data):
        # Validate transaction exists and is eligible
        try:
            txn = TransactionDetail.objects.get(txn_id=data['txn_id'])
            
            if txn.status != 'SUCCESS':
                raise serializers.ValidationError("Only successful transactions can be refunded")
            
            if txn.is_refunded:
                raise serializers.ValidationError("Transaction already refunded")
            
            if data['refund_type'] == 'FULL':
                data['refund_amount'] = txn.paid_amount
            elif data['refund_amount'] > txn.paid_amount:
                raise serializers.ValidationError("Refund amount exceeds transaction amount")
            
            # Check refund window
            from datetime import timedelta
            from django.utils import timezone
            
            config = RefundConfiguration.objects.filter(client_id=txn.client_id).first()
            if config:
                max_days = config.max_refund_days
                if txn.created_date < timezone.now() - timedelta(days=max_days):
                    raise serializers.ValidationError(f"Refund window expired (max {max_days} days)")
            
        except TransactionDetail.DoesNotExist:
            raise serializers.ValidationError("Transaction not found")
        
        return data

class ApproveRefundSerializer(serializers.Serializer):
    refund_id = serializers.IntegerField()
    action = serializers.ChoiceField(choices=['APPROVE', 'REJECT', 'ESCALATE'])
    comments = serializers.CharField(required=False)
    rejection_reason = serializers.CharField(required=False)

class RefundStatusSerializer(serializers.Serializer):
    total_requests = serializers.IntegerField()
    pending_approval = serializers.IntegerField()
    processing = serializers.IntegerField()
    completed = serializers.IntegerField()
    rejected = serializers.IntegerField()
    total_amount_refunded = serializers.DecimalField(max_digits=15, decimal_places=2)
    pending_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    average_processing_time_hours = serializers.FloatField()

class RefundReportSerializer(serializers.Serializer):
    date = serializers.DateField()
    requests_count = serializers.IntegerField()
    approved_count = serializers.IntegerField()
    rejected_count = serializers.IntegerField()
    completed_count = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2)

class RefundTrackingSerializer(serializers.Serializer):
    refund_id = serializers.IntegerField()
    track_id = serializers.CharField()
    txn_id = serializers.CharField()
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    status = serializers.CharField()
    request_date = serializers.DateTimeField()
    approved_date = serializers.DateTimeField(required=False)
    pg_refund_id = serializers.CharField(required=False)
    pg_status = serializers.CharField(required=False)
    timeline = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )