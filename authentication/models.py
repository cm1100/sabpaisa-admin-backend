"""
Authentication Models - Following SOLID Principles
Single Responsibility: Each model handles one aspect of authentication
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid


class AdminUser(AbstractUser):
    """
    Custom User model for admin users
    Single Responsibility: User data management only
    """
    user_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    role = models.CharField(max_length=50, choices=[
        ('super_admin', 'Super Admin'),
        ('operations_manager', 'Operations Manager'),
        ('settlement_admin', 'Settlement Admin'),
        ('client_manager', 'Client Manager'),
        ('compliance_officer', 'Compliance Officer'),
        ('auditor', 'Auditor'),
        ('viewer', 'Viewer'),
    ], default='viewer')
    
    mfa_enabled = models.BooleanField(default=False)
    mfa_secret = models.CharField(max_length=255, blank=True, null=True)
    
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'admin_users'
        verbose_name = 'Admin User'
        verbose_name_plural = 'Admin Users'
    
    def __str__(self):
        return f"{self.username} ({self.role})"


class RefreshToken(models.Model):
    """
    Refresh token storage
    Single Responsibility: Token persistence only
    """
    token_id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    user = models.ForeignKey(AdminUser, on_delete=models.CASCADE, related_name='refresh_tokens')
    token = models.TextField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    revoked = models.BooleanField(default=False)
    revoked_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'refresh_tokens'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', 'revoked']),
        ]
    
    def is_valid(self):
        """Check if token is valid"""
        if self.revoked:
            return False
        if self.expires_at < timezone.now():
            return False
        return True
    
    def revoke(self):
        """Revoke the token"""
        self.revoked = True
        self.revoked_at = timezone.now()
        self.save(update_fields=['revoked', 'revoked_at'])


class LoginAttempt(models.Model):
    """
    Login attempt tracking for security
    Single Responsibility: Security tracking only
    """
    username = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField()
    success = models.BooleanField(default=False)
    attempted_at = models.DateTimeField(auto_now_add=True)
    failure_reason = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        db_table = 'login_attempts'
        indexes = [
            models.Index(fields=['username', 'attempted_at']),
            models.Index(fields=['ip_address', 'attempted_at']),
        ]
        ordering = ['-attempted_at']