from rest_framework import serializers
from .models import FeeConfiguration, FeeCalculationLog, PromotionalFees, FeeReconciliation
from decimal import Decimal
from datetime import datetime
from django.utils import timezone

class FeeConfigurationSerializer(serializers.ModelSerializer):
    is_currently_active = serializers.ReadOnlyField()
    calculated_fee_preview = serializers.SerializerMethodField()
    
    class Meta:
        model = FeeConfiguration
        fields = '__all__'
        read_only_fields = ['fee_id', 'created_at', 'updated_at', 'created_by', 'approved_by']
    
    def get_calculated_fee_preview(self, obj):
        """Preview fee calculation for different amounts"""
        if not obj.is_currently_active:
            return None
        
        preview = []
        test_amounts = [100, 1000, 5000, 10000, 50000]
        
        for amount in test_amounts:
            try:
                fee = obj.calculate_fee(amount)
                preview.append({
                    'amount': amount,
                    'fee': float(fee),
                    'total': float(amount + fee)
                })
            except:
                pass
        
        return preview
    
    def validate_tier_rates(self, value):
        """Validate tier rates structure"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Tier rates must be a list")
        
        for tier in value:
            if not all(key in tier for key in ['min', 'rate']):
                raise serializers.ValidationError("Each tier must have 'min' and 'rate' fields")
        
        return value
    
    def validate_effective_dates(self, attrs):
        """Validate effective date range"""
        effective_from = attrs.get('effective_from')
        effective_until = attrs.get('effective_until')
        
        if effective_until and effective_from >= effective_until:
            raise serializers.ValidationError("Effective until must be after effective from")
        
        return attrs


class FeeCalculationLogSerializer(serializers.ModelSerializer):
    fee_configuration = serializers.SerializerMethodField()
    
    class Meta:
        model = FeeCalculationLog
        fields = '__all__'
        read_only_fields = ['calc_id', 'created_at']
    
    def get_fee_configuration(self, obj):
        """Get associated fee configuration details"""
        try:
            config = FeeConfiguration.objects.get(fee_id=obj.fee_id)
            return {
                'fee_name': config.fee_name,
                'fee_type': config.fee_type,
                'fee_structure': config.fee_structure
            }
        except FeeConfiguration.DoesNotExist:
            return None


class PromotionalFeesSerializer(serializers.ModelSerializer):
    is_valid = serializers.ReadOnlyField()
    usage_percentage = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = PromotionalFees
        fields = '__all__'
        read_only_fields = ['promo_id', 'created_at', 'updated_at', 'used_count', 'created_by']
    
    def get_usage_percentage(self, obj):
        """Calculate usage percentage"""
        if obj.usage_limit == 0:
            return 0
        return round((obj.used_count / obj.usage_limit) * 100, 2)
    
    def get_days_remaining(self, obj):
        """Calculate days remaining until expiry"""
        if obj.valid_until:
            delta = obj.valid_until - timezone.now()
            return max(0, delta.days)
        return None
    
    def validate_promo_code(self, value):
        """Validate promo code format"""
        if not value.isalnum():
            raise serializers.ValidationError("Promo code must be alphanumeric")
        return value.upper()
    
    def validate_discount_value(self, value):
        """Validate discount value based on type"""
        if value <= 0:
            raise serializers.ValidationError("Discount value must be positive")
        
        # Additional validation based on discount type would go here
        return value
    
    def validate(self, attrs):
        """Cross-field validation"""
        valid_from = attrs.get('valid_from')
        valid_until = attrs.get('valid_until')
        
        if valid_from and valid_until and valid_from >= valid_until:
            raise serializers.ValidationError("Valid until must be after valid from")
        
        discount_type = attrs.get('discount_type')
        discount_value = attrs.get('discount_value')
        
        if discount_type == 'PERCENTAGE' and discount_value > 100:
            raise serializers.ValidationError("Percentage discount cannot exceed 100%")
        
        return attrs


class FeeReconciliationSerializer(serializers.ModelSerializer):
    variance_status = serializers.SerializerMethodField()
    fee_breakdown_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = FeeReconciliation
        fields = '__all__'
        read_only_fields = ['recon_id', 'created_at', 'updated_at', 'variance', 'variance_percentage']
    
    def get_variance_status(self, obj):
        """Categorize variance status"""
        if abs(obj.variance_percentage) < 1:
            return 'ACCEPTABLE'
        elif abs(obj.variance_percentage) < 5:
            return 'WARNING'
        else:
            return 'CRITICAL'
    
    def get_fee_breakdown_summary(self, obj):
        """Summarize fee breakdown"""
        if not obj.fee_breakdown:
            return None
        
        total = sum(obj.fee_breakdown.values())
        summary = {}
        
        for fee_type, amount in obj.fee_breakdown.items():
            percentage = (amount / total * 100) if total > 0 else 0
            summary[fee_type] = {
                'amount': amount,
                'percentage': round(percentage, 2)
            }
        
        return summary


class FeeCalculatorSerializer(serializers.Serializer):
    """Serializer for fee calculation requests"""
    client_id = serializers.CharField(max_length=50)
    transaction_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    payment_method = serializers.CharField(max_length=50, required=False)
    fee_type = serializers.CharField(max_length=20, default='TRANSACTION')
    promo_code = serializers.CharField(max_length=50, required=False, allow_blank=True)
    volume_data = serializers.JSONField(required=False)
    
    def validate_transaction_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Transaction amount must be positive")
        return value


class BulkFeeUpdateSerializer(serializers.Serializer):
    """Serializer for bulk fee updates"""
    client_ids = serializers.ListField(
        child=serializers.CharField(max_length=50),
        min_length=1
    )
    fee_type = serializers.CharField(max_length=20)
    updates = serializers.JSONField()
    effective_from = serializers.DateTimeField()
    reason = serializers.CharField(max_length=500)
    
    def validate_updates(self, value):
        required_fields = ['base_rate']
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f"Missing required field: {field}")
        return value


class FeeComparisonSerializer(serializers.Serializer):
    """Serializer for fee comparison across clients"""
    client_ids = serializers.ListField(
        child=serializers.CharField(max_length=50),
        min_length=2,
        max_length=10
    )
    fee_types = serializers.ListField(
        child=serializers.CharField(max_length=20),
        required=False
    )
    comparison_date = serializers.DateTimeField(required=False, default=timezone.now)