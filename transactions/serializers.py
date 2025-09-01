"""
Transaction Serializers
Following DRF best practices with proper validation
"""
from rest_framework import serializers
from .models import TransactionDetail, RefundRequestFromClient, SettledTransactions, TransactionsToSettle


class TransactionDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for transaction details
    """
    formatted_amount = serializers.ReadOnlyField()
    is_successful = serializers.ReadOnlyField()
    
    class Meta:
        model = TransactionDetail
        fields = [
            'txn_id', 'client_txn_id', 'pg_txn_id', 'bank_txn_id', 'client_id', 
            'client_code', 'client_name', 'payee_amount', 'paid_amount', 'act_amount',
            'convcharges', 'ep_charges', 'gst', 'settlement_amount', 'is_settled',
            'settlement_date', 'settlement_status', 'payment_mode', 'pg_pay_mode',
            'pg_name', 'bank_name', 'payee_first_name', 'payee_email', 'payee_mob',
            'status', 'pg_response_code', 'sabpaisa_resp_code', 'resp_msg',
            'refund_status_code', 'refund_date', 'refunded_amount', 'is_charge_back',
            'charge_back_amount', 'trans_date', 'trans_complete_date', 
            'formatted_amount', 'is_successful'
        ]
        read_only_fields = ['txn_id', 'trans_date']


class TransactionListSerializer(serializers.Serializer):
    """
    Serializer for transaction list with pagination (works with dictionary data)
    """
    txn_id = serializers.CharField()
    amount = serializers.FloatField()
    status = serializers.CharField()
    payment_mode = serializers.CharField()
    client_code = serializers.CharField()
    payee_name = serializers.CharField()
    payee_email = serializers.EmailField()
    payee_mob = serializers.CharField()
    trans_date = serializers.CharField()  # Already serialized as ISO string
    pg_name = serializers.CharField()
    formatted_amount = serializers.SerializerMethodField()
    is_settled = serializers.BooleanField()
    
    def get_formatted_amount(self, obj):
        """Get formatted amount from dictionary data"""
        amount = obj.get('amount', 0)
        return f"₹{float(amount):,.2f}"


class TransactionStatsSerializer(serializers.Serializer):
    """
    Serializer for transaction statistics
    """
    total_transactions = serializers.IntegerField()
    total_amount = serializers.FloatField()
    average_amount = serializers.FloatField()
    success_count = serializers.IntegerField()
    failed_count = serializers.IntegerField()
    pending_count = serializers.IntegerField()
    success_rate = serializers.FloatField()
    date_range = serializers.CharField()


class TransactionFilterSerializer(serializers.Serializer):
    """
    Serializer for transaction filters
    """
    status = serializers.ChoiceField(
        choices=['SUCCESS', 'FAILED', 'PENDING', 'REFUNDED', 'CANCELLED'],
        required=False
    )
    client_code = serializers.CharField(required=False)
    date_from = serializers.DateTimeField(required=False)
    date_to = serializers.DateTimeField(required=False)
    search = serializers.CharField(required=False)
    page = serializers.IntegerField(default=1, min_value=1)
    page_size = serializers.IntegerField(default=20, min_value=1, max_value=100)


class RefundSerializer(serializers.ModelSerializer):
    """
    Serializer for refund transactions
    """
    
    class Meta:
        model = RefundRequestFromClient
        fields = [
            'refund_id', 'txn_id', 'client_id', 'refund_amount', 
            'refund_reason', 'request_date', 'approval_status',
            'approved_by', 'approved_date', 'processed_date', 'bank_ref'
        ]
        read_only_fields = ['refund_id', 'request_date']


class InitiateRefundSerializer(serializers.Serializer):
    """
    Serializer for initiating refunds
    """
    txn_id = serializers.CharField(required=True)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    reason = serializers.CharField(required=True, max_length=500)
    
    def validate_amount(self, value):
        """Validate refund amount is positive"""
        if value <= 0:
            raise serializers.ValidationError("Refund amount must be positive")
        return value


class DisputeSerializer(serializers.Serializer):
    """
    Serializer for transaction disputes
    """
    txn_id = serializers.CharField()
    dispute_type = serializers.CharField()
    dispute_reason = serializers.CharField()
    dispute_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    dispute_status = serializers.CharField()
    raised_by = serializers.CharField()
    raised_at = serializers.DateTimeField()
    resolved_at = serializers.DateTimeField(required=False)
    resolution_notes = serializers.CharField(required=False)


class CreateDisputeSerializer(serializers.Serializer):
    """
    Serializer for creating disputes
    """
    txn_id = serializers.CharField(required=True)
    dispute_type = serializers.ChoiceField(
        choices=['CHARGEBACK', 'FRAUD', 'DUPLICATE', 'QUALITY', 'OTHER'],
        required=True
    )
    reason = serializers.CharField(required=True, max_length=1000)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    
    def validate_amount(self, value):
        """Validate dispute amount is positive"""
        if value <= 0:
            raise serializers.ValidationError("Dispute amount must be positive")
        return value


class PaymentModeDistributionSerializer(serializers.Serializer):
    """
    Serializer for payment mode distribution analytics
    """
    payment_mode = serializers.CharField()
    count = serializers.IntegerField()
    total_amount = serializers.FloatField()


class HourlyVolumeSerializer(serializers.Serializer):
    """
    Serializer for hourly transaction volume
    """
    hour = serializers.CharField()
    date = serializers.DateField()
    count = serializers.IntegerField()
    amount = serializers.FloatField()


class TopClientSerializer(serializers.Serializer):
    """
    Serializer for top clients by volume
    """
    client_code = serializers.CharField()
    transaction_count = serializers.IntegerField()
    total_amount = serializers.FloatField()
    success_rate = serializers.FloatField()


class TransactionExportSerializer(serializers.Serializer):
    """
    Serializer for transaction export parameters
    """
    format = serializers.ChoiceField(choices=['csv', 'excel', 'pdf'], default='csv')
    date_from = serializers.DateTimeField(required=False)
    date_to = serializers.DateTimeField(required=False)
    status = serializers.CharField(required=False)
    client_code = serializers.CharField(required=False)


# Settlement Serializers
class SettlementSummarySerializer(serializers.Serializer):
    """
    Serializer for settlement summary data
    """
    pending_count = serializers.IntegerField()
    pending_amount = serializers.FloatField()
    settled_today_count = serializers.IntegerField()
    settled_today_amount = serializers.FloatField()
    settled_week_count = serializers.IntegerField()
    settled_week_amount = serializers.FloatField()
    settled_month_count = serializers.IntegerField()
    settled_month_amount = serializers.FloatField()
    in_process_count = serializers.IntegerField()
    in_process_amount = serializers.FloatField()


class PendingSettlementSerializer(serializers.Serializer):
    """
    Serializer for pending settlements
    """
    txn_id = serializers.CharField()
    client_id = serializers.CharField()
    client_name = serializers.CharField()
    client_code = serializers.CharField()
    paid_amount = serializers.FloatField()
    settlement_amount = serializers.FloatField()
    payee_name = serializers.CharField()
    payee_email = serializers.EmailField()
    payee_mob = serializers.CharField()
    trans_date = serializers.DateTimeField()
    payment_mode = serializers.CharField()
    status = serializers.CharField()
    age_in_days = serializers.IntegerField()
    formatted_amount = serializers.CharField()


class SettledTransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for settled transactions
    """
    formatted_amount = serializers.SerializerMethodField()
    settlement_date_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = SettledTransactions
        fields = [
            'id', 'transaction_id', 'bank_name', 'transaction_mode',
            'trans_date', 'net_amount', 'gross_amount', 'currency',
            'conv_fee', 'gst_fee', 'pipe_fee', 'transaction_status',
            'payout_status', 'name', 'email', 'mobile_number',
            'settlement_amount', 'payment_date', 'formatted_amount',
            'settlement_date_formatted'
        ]
    
    def get_formatted_amount(self, obj):
        amount = obj.settlement_amount or obj.net_amount or 0
        return f"₹{amount:,.2f}"
    
    def get_settlement_date_formatted(self, obj):
        if obj.trans_date:
            # Handle both date and datetime objects
            if hasattr(obj.trans_date, 'strftime'):
                if hasattr(obj.trans_date, 'hour'):  # datetime
                    return obj.trans_date.strftime('%d %b %Y %H:%M')
                else:  # date
                    return obj.trans_date.strftime('%d %b %Y')
        return None


class TransactionsToSettleSerializer(serializers.ModelSerializer):
    """
    Serializer for transactions in settlement queue
    """
    formatted_amount = serializers.SerializerMethodField()
    queue_age = serializers.SerializerMethodField()
    
    class Meta:
        model = TransactionsToSettle
        fields = [
            'id', 'transaction_id', 'client_code', 'client_name',
            'payee_name', 'payee_email', 'payee_mobile',
            'paid_amount', 'settlement_amount', 'payment_mode',
            'transaction_status', 'payout_status', 'trans_date',
            'settlement_date', 'settlement_status', 'formatted_amount',
            'queue_age'
        ]
    
    def get_formatted_amount(self, obj):
        amount = obj.settlement_amount or obj.paid_amount or 0
        return f"₹{amount:,.2f}"
    
    def get_queue_age(self, obj):
        if obj.trans_date:
            from datetime import datetime
            from django.utils import timezone
            now = timezone.now()
            return (now - obj.trans_date).days
        return 0


class ClientSettlementSummarySerializer(serializers.Serializer):
    """
    Serializer for client-wise settlement summary
    """
    client_id = serializers.CharField()
    client_name = serializers.CharField()
    client_code = serializers.CharField()
    pending_count = serializers.IntegerField()
    pending_amount = serializers.FloatField()
    settled_count = serializers.IntegerField()
    settled_amount = serializers.FloatField()
    last_settlement_date = serializers.DateTimeField(allow_null=True)
    formatted_pending_amount = serializers.CharField()
    formatted_settled_amount = serializers.CharField()


class BatchSettlementRequestSerializer(serializers.Serializer):
    """
    Serializer for batch settlement requests
    """
    transaction_ids = serializers.ListField(
        child=serializers.CharField(),
        min_length=1,
        max_length=100
    )
    settlement_date = serializers.DateTimeField(required=False)
    remarks = serializers.CharField(required=False, max_length=500)
    
    def validate_transaction_ids(self, value):
        """Validate that all transaction IDs exist and are eligible"""
        if len(value) > 100:
            raise serializers.ValidationError("Cannot process more than 100 transactions at once")
        
        # Check if transactions exist and are eligible
        from .models import TransactionDetail
        existing_txns = TransactionDetail.objects.filter(
            txn_id__in=value,
            status='SUCCESS',
            is_settled=False
        ).values_list('txn_id', flat=True)
        
        missing_txns = set(value) - set(existing_txns)
        if missing_txns:
            raise serializers.ValidationError(
                f"Transaction IDs not found or not eligible for settlement: {list(missing_txns)}"
            )
        
        return value


class SettlementBatchSerializer(serializers.Serializer):
    """
    Serializer for settlement batch information
    """
    batch_id = serializers.CharField()
    settlement_date = serializers.DateTimeField()
    total_transactions = serializers.IntegerField()
    total_amount = serializers.FloatField()
    status = serializers.CharField()
    created_at = serializers.DateTimeField()
    processed_transactions = serializers.ListField(
        child=serializers.CharField()
    )
    failed_transactions = serializers.ListField(
        child=serializers.DictField()
    )


class AddToQueueSerializer(serializers.Serializer):
    """
    Serializer for adding transactions to settlement queue
    """
    transaction_ids = serializers.ListField(
        child=serializers.CharField(),
        min_length=1
    )
    scheduled_for = serializers.DateTimeField(required=False)
    priority = serializers.ChoiceField(
        choices=[('HIGH', 'High'), ('NORMAL', 'Normal'), ('LOW', 'Low')],
        default='NORMAL'
    )