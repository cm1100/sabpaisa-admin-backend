"""
Authentication Serializers - Following SOLID Principles
Single Responsibility: Each serializer handles one type of data
"""
from rest_framework import serializers
from .models import AdminUser
from .mfa_models import MFADevice, BackupCode, TrustedDevice, MFAConfiguration


class LoginSerializer(serializers.Serializer):
    """
    Login request serializer
    Single Responsibility: Only validates login data
    """
    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        """Ensure either username or email is provided"""
        if not attrs.get('username') and not attrs.get('email'):
            raise serializers.ValidationError('Either username or email is required')
        return attrs


class TokenSerializer(serializers.Serializer):
    """
    Token response serializer
    Interface Segregation: Specific serializer for token response
    """
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    token_type = serializers.CharField(default='Bearer')
    expires_in = serializers.IntegerField(default=900)  # 15 minutes


class UserSerializer(serializers.ModelSerializer):
    """
    User data serializer
    Open/Closed: Can be extended for additional fields
    """
    class Meta:
        model = AdminUser
        fields = ['user_id', 'username', 'email', 'first_name', 'last_name', 'role']
        read_only_fields = ['user_id']


class LoginResponseSerializer(serializers.Serializer):
    """
    Complete login response serializer
    Liskov Substitution: Can replace base serializer
    """
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    token_type = serializers.CharField(default='Bearer')
    expires_in = serializers.IntegerField(default=900)
    user = UserSerializer()


class RefreshTokenSerializer(serializers.Serializer):
    """Refresh token request serializer"""
    refresh_token = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    """Logout request serializer"""
    refresh_token = serializers.CharField(required=False)


class MFASetupSerializer(serializers.Serializer):
    """MFA Setup request serializer"""
    device_name = serializers.CharField(max_length=100, default="Default")


class MFAVerifySetupSerializer(serializers.Serializer):
    """MFA Setup verification serializer"""
    device_id = serializers.IntegerField()
    token = serializers.CharField(max_length=6)


class MFAVerifySerializer(serializers.Serializer):
    """MFA verification serializer for login"""
    token = serializers.CharField(max_length=6)
    trust_device = serializers.BooleanField(default=False)
    device_info = serializers.JSONField(required=False)


class MFADeviceSerializer(serializers.ModelSerializer):
    """MFA Device serializer"""
    class Meta:
        model = MFADevice
        fields = ['id', 'device_name', 'device_type', 'is_primary',
                  'is_active', 'last_used_at', 'created_at']
        read_only_fields = ['id', 'last_used_at', 'created_at']


class BackupCodeSerializer(serializers.ModelSerializer):
    """Backup Code serializer"""
    class Meta:
        model = BackupCode
        fields = ['code', 'is_used', 'used_at', 'created_at']
        read_only_fields = ['used_at', 'created_at']


class TrustedDeviceSerializer(serializers.ModelSerializer):
    """Trusted Device serializer"""
    class Meta:
        model = TrustedDevice
        fields = ['id', 'device_name', 'device_type', 'browser', 'os',
                  'location', 'last_used_at', 'created_at', 'expires_at']
        read_only_fields = ['id', 'last_used_at', 'created_at']


class MFAConfigurationSerializer(serializers.ModelSerializer):
    """MFA Configuration serializer"""
    class Meta:
        model = MFAConfiguration
        fields = ['is_enabled', 'require_mfa_for_login', 'require_mfa_for_transactions',
                  'require_mfa_for_settlements', 'require_mfa_for_configuration',
                  'max_attempts', 'lockout_duration', 'trusted_device_duration',
                  'backup_codes_count']
        read_only_fields = ['created_at', 'updated_at']