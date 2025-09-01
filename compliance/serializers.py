from rest_framework import serializers
from .models import (
    TransactionDetail, ClientDataTable, 
    AdminUserActivityLog, ComplianceAlert, RBIReportLog
)


class KYCStatusSerializer(serializers.Serializer):
    total_clients = serializers.IntegerField()
    verified = serializers.IntegerField()
    pending = serializers.IntegerField()
    rejected = serializers.IntegerField()
    expired = serializers.IntegerField()
    verification_rate = serializers.FloatField()


class SuspiciousTransactionSerializer(serializers.ModelSerializer):
    risk_indicators = serializers.ListField(child=serializers.CharField())
    
    class Meta:
        model = TransactionDetail
        fields = [
            'txn_id', 'client_name', 'paid_amount', 'payment_mode',
            'risk_score', 'created_date', 'risk_indicators'
        ]


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminUserActivityLog
        fields = '__all__'


class ComplianceAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplianceAlert
        fields = '__all__'
        read_only_fields = ['alert_id', 'detected_at']


class ComplianceDashboardSerializer(serializers.Serializer):
    kyc_summary = KYCStatusSerializer()
    risk_distribution = serializers.DictField()
    recent_alerts = ComplianceAlertSerializer(many=True)
    suspicious_transactions = serializers.ListField()
    compliance_score = serializers.FloatField()
    pending_reviews = serializers.IntegerField()


class RBIReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = RBIReportLog
        fields = '__all__'


class ComplianceReviewSerializer(serializers.Serializer):
    alert_id = serializers.IntegerField()
    action = serializers.ChoiceField(choices=['RESOLVE', 'ESCALATE', 'FALSE_POSITIVE'])
    comments = serializers.CharField()
    

class TransactionRiskAnalysisSerializer(serializers.Serializer):
    txn_id = serializers.CharField()
    risk_score = serializers.IntegerField()
    risk_factors = serializers.ListField(child=serializers.DictField())
    recommendation = serializers.CharField()