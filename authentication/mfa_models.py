"""
Multi-Factor Authentication Models
Implements TOTP-based MFA with backup codes
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import pyotp
import secrets
import string
from cryptography.fernet import Fernet
from django.conf import settings

User = get_user_model()


class MFADevice(models.Model):
    """
    MFA device registration for users
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mfa_devices')
    device_name = models.CharField(max_length=100)
    device_type = models.CharField(max_length=50, default='totp')
    secret_key = models.CharField(max_length=255)  # Encrypted
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    DEVICE_TYPES = [
        ('totp', 'Time-based OTP'),
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('backup', 'Backup Codes'),
    ]
    
    class Meta:
        db_table = 'mfa_devices'
        ordering = ['-is_primary', '-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.device_name}"
    
    def generate_secret(self):
        """Generate a new TOTP secret"""
        secret = pyotp.random_base32()
        self.secret_key = self.encrypt_secret(secret)
        return secret
    
    def encrypt_secret(self, secret):
        """Encrypt the secret key"""
        # In production, use proper key management
        key = getattr(settings, 'MFA_ENCRYPTION_KEY', Fernet.generate_key())
        f = Fernet(key)
        return f.encrypt(secret.encode()).decode()
    
    def decrypt_secret(self):
        """Decrypt the secret key"""
        key = getattr(settings, 'MFA_ENCRYPTION_KEY', Fernet.generate_key())
        f = Fernet(key)
        return f.decrypt(self.secret_key.encode()).decode()
    
    def verify_token(self, token):
        """Verify TOTP token"""
        if self.device_type == 'totp':
            totp = pyotp.TOTP(self.decrypt_secret())
            # Allow for time drift
            return totp.verify(token, valid_window=1)
        return False
    
    def get_provisioning_uri(self, issuer='SabPaisa Admin'):
        """Get provisioning URI for QR code"""
        if self.device_type == 'totp':
            totp = pyotp.TOTP(self.decrypt_secret())
            return totp.provisioning_uri(
                name=self.user.email or self.user.username,
                issuer_name=issuer
            )
        return None


class BackupCode(models.Model):
    """
    Backup codes for account recovery
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='backup_codes')
    code = models.CharField(max_length=12, unique=True)
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'mfa_backup_codes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_used']),
            models.Index(fields=['code']),
        ]
    
    @classmethod
    def generate_codes_for_user(cls, user, count=10):
        """Generate backup codes for a user"""
        codes = []
        for _ in range(count):
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(12))
            backup_code = cls.objects.create(user=user, code=code)
            codes.append(code)
        return codes
    
    def use_code(self):
        """Mark code as used"""
        self.is_used = True
        self.used_at = timezone.now()
        self.save()
        return True


class MFAChallenge(models.Model):
    """
    Track MFA challenges for enhanced security
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mfa_challenges')
    challenge_type = models.CharField(max_length=50)
    challenge_code = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    is_successful = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    CHALLENGE_TYPES = [
        ('login', 'Login'),
        ('transaction', 'Transaction'),
        ('settlement', 'Settlement'),
        ('configuration', 'Configuration Change'),
        ('bulk_operation', 'Bulk Operation'),
    ]
    
    class Meta:
        db_table = 'mfa_challenges'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['challenge_code']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.challenge_type} - {self.created_at}"


class TrustedDevice(models.Model):
    """
    Remember trusted devices for users
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trusted_devices')
    device_id = models.CharField(max_length=255, unique=True)
    device_name = models.CharField(max_length=100)
    device_type = models.CharField(max_length=50)  # mobile, desktop, tablet
    browser = models.CharField(max_length=100)
    os = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField()
    location = models.CharField(max_length=255, blank=True)
    trust_token = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'mfa_trusted_devices'
        ordering = ['-last_used_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['device_id']),
            models.Index(fields=['trust_token']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.device_name}"
    
    @classmethod
    def create_trust_token(cls):
        """Generate a unique trust token"""
        return secrets.token_urlsafe(32)
    
    def is_valid(self):
        """Check if device trust is still valid"""
        return self.is_active and self.expires_at > timezone.now()
    
    def renew(self):
        """Renew device trust"""
        self.expires_at = timezone.now() + timezone.timedelta(days=30)
        self.last_used_at = timezone.now()
        self.save()


class MFAConfiguration(models.Model):
    """
    Global MFA configuration and policies
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='mfa_config')
    is_enabled = models.BooleanField(default=False)
    require_mfa_for_login = models.BooleanField(default=True)
    require_mfa_for_transactions = models.BooleanField(default=True)
    require_mfa_for_settlements = models.BooleanField(default=True)
    require_mfa_for_configuration = models.BooleanField(default=True)
    max_attempts = models.IntegerField(default=3)
    lockout_duration = models.IntegerField(default=300)  # seconds
    trusted_device_duration = models.IntegerField(default=30)  # days
    backup_codes_count = models.IntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'mfa_configurations'
    
    def __str__(self):
        return f"MFA Config for {self.user.username}"