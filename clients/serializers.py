"""
Client Serializers - Following SOLID Principles
Single Responsibility: Each serializer handles one aspect of serialization
"""
from rest_framework import serializers
from .models import ClientDataTable, ClientPaymentMode, ClientFeeBearer


class ClientPaymentModeSerializer(serializers.ModelSerializer):
    """Payment mode serializer"""
    class Meta:
        model = ClientPaymentMode
        fields = ['epid', 'payment_mode', 'enable', 'created_date']
        read_only_fields = ['epid', 'created_date']


class ClientFeeBearerSerializer(serializers.ModelSerializer):
    """Fee bearer serializer"""
    class Meta:
        model = ClientFeeBearer
        fields = ['id', 'paymode', 'bearer', 'created_date', 'updated_date']
        read_only_fields = ['id', 'created_date', 'updated_date']


class ClientListSerializer(serializers.ModelSerializer):
    """
    Client list serializer - Optimized for list views
    Interface Segregation: Specific serializer for list operations
    """
    payment_modes_count = serializers.IntegerField(read_only=True, default=0)
    
    class Meta:
        model = ClientDataTable
        fields = [
            'client_id', 'client_code', 'client_name', 'client_type',
            'client_email', 'client_contact', 'active', 'risk_category',
            'creation_date', 'payment_modes_count'
        ]


class ClientDetailSerializer(serializers.ModelSerializer):
    """
    Client detail serializer - Full client information
    Single Responsibility: Only handles detailed serialization
    """
    payment_modes = ClientPaymentModeSerializer(many=True, read_only=True)
    fee_bearers = ClientFeeBearerSerializer(many=True, read_only=True)
    
    class Meta:
        model = ClientDataTable
        fields = '__all__'
        read_only_fields = ['client_id', 'creation_date', 'update_date']


class ClientCreateSerializer(serializers.ModelSerializer):
    """
    Client creation serializer with validation
    Open/Closed: Can be extended for additional validation
    """
    # Make complex fields optional for easier integration
    auth_key = serializers.CharField(required=False, allow_blank=True)
    auth_iv = serializers.CharField(required=False, allow_blank=True)
    client_user_name = serializers.CharField(required=False, allow_blank=True)
    client_pass = serializers.CharField(required=False, allow_blank=True)
    success_ru_url = serializers.URLField(required=False, allow_blank=True)
    failed_ru_url = serializers.URLField(required=False, allow_blank=True)
    push_api_url = serializers.URLField(required=False, allow_blank=True)
    client_logo_path = serializers.CharField(required=False, allow_blank=True)
    risk_category = serializers.IntegerField(required=False, default=1)
    active = serializers.BooleanField(default=True)
    
    class Meta:
        model = ClientDataTable
        fields = [
            'client_code', 'client_name', 'client_type', 'client_email',
            'client_contact', 'client_address', 'risk_category', 'active',
            'auth_key', 'auth_iv', 'client_user_name', 'client_pass',
            'success_ru_url', 'failed_ru_url', 'push_api_url', 'client_logo_path'
        ]
    
    def validate_client_email(self, value):
        """Email validation"""
        if '@' not in value:
            raise serializers.ValidationError("Invalid email format")
        return value
    
    def validate_risk_category(self, value):
        """Risk category validation"""
        if value and not 1 <= value <= 5:
            raise serializers.ValidationError("Risk category must be between 1 and 5")
        return value


class ClientUpdateSerializer(serializers.ModelSerializer):
    """
    Client update serializer
    Liskov Substitution: Can replace base serializer
    """
    # Make all fields optional for partial updates
    client_name = serializers.CharField(required=False)
    client_type = serializers.CharField(required=False)
    client_email = serializers.EmailField(required=False)
    client_contact = serializers.CharField(required=False)
    client_address = serializers.CharField(required=False, allow_blank=True)
    risk_category = serializers.IntegerField(required=False)
    active = serializers.BooleanField(required=False)
    push_api_url = serializers.URLField(required=False, allow_blank=True)
    success_ru_url = serializers.URLField(required=False, allow_blank=True)
    failed_ru_url = serializers.URLField(required=False, allow_blank=True)
    
    class Meta:
        model = ClientDataTable
        fields = [
            'client_name', 'client_type', 'client_email', 'client_contact',
            'client_address', 'risk_category', 'active', 'push_api_url',
            'success_ru_url', 'failed_ru_url'
        ]


class ClientBulkOperationSerializer(serializers.Serializer):
    """
    Bulk operation serializer
    Single Responsibility: Only handles bulk operation validation
    """
    client_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        max_length=100
    )
    operation = serializers.ChoiceField(
        choices=['activate', 'deactivate', 'delete']
    )


class ClientCloneSerializer(serializers.Serializer):
    """
    Client clone serializer
    Interface Segregation: Specific serializer for cloning
    """
    source_client_id = serializers.IntegerField()
    new_client_code = serializers.CharField(max_length=50)
    new_client_name = serializers.CharField(max_length=255, required=False)


class ClientStatisticsSerializer(serializers.Serializer):
    """Statistics response serializer"""
    total_clients = serializers.IntegerField()
    active_clients = serializers.IntegerField()
    inactive_clients = serializers.IntegerField()
    by_type = serializers.ListField()
    by_risk_category = serializers.ListField()