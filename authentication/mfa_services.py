"""
MFA Services
Business logic for Multi-Factor Authentication
"""
import pyotp
import qrcode
import io
import base64
from typing import Optional, Dict, Any, List
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta
import logging

from .mfa_models import (
    MFADevice, BackupCode, MFAChallenge,
    TrustedDevice, MFAConfiguration
)

User = get_user_model()
logger = logging.getLogger(__name__)


class MFAService:
    """
    Service for managing MFA operations
    """
    
    def setup_mfa(self, user: User, device_name: str = "Default") -> Dict[str, Any]:
        """
        Setup MFA for a user
        """
        try:
            # Check if user already has MFA
            config, _ = MFAConfiguration.objects.get_or_create(user=user)
            
            # Create MFA device
            device = MFADevice(
                user=user,
                device_name=device_name,
                device_type='totp'
            )
            
            # Generate secret
            secret = device.generate_secret()
            device.save()
            
            # Generate backup codes
            backup_codes = BackupCode.generate_codes_for_user(user)
            
            # Generate QR code
            provisioning_uri = device.get_provisioning_uri()
            qr_code = self.generate_qr_code(provisioning_uri)
            
            return {
                'device_id': device.id,
                'secret': secret,
                'qr_code': qr_code,
                'provisioning_uri': provisioning_uri,
                'backup_codes': backup_codes,
                'status': 'pending_verification'
            }
            
        except Exception as e:
            logger.error(f"Error setting up MFA for user {user.id}: {str(e)}")
            raise
    
    def verify_setup(self, user: User, device_id: int, token: str) -> bool:
        """
        Verify MFA setup with initial token
        """
        try:
            device = MFADevice.objects.get(id=device_id, user=user)
            
            if device.verify_token(token):
                device.verified_at = timezone.now()
                device.is_active = True
                device.save()
                
                # Enable MFA for user
                config = MFAConfiguration.objects.get(user=user)
                config.is_enabled = True
                config.save()
                
                return True
            
            return False
            
        except MFADevice.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"Error verifying MFA setup: {str(e)}")
            return False
    
    def verify_mfa(self, user: User, token: str, challenge_type: str = 'login',
                   ip_address: str = None, user_agent: str = None) -> Dict[str, Any]:
        """
        Verify MFA token for authentication
        """
        try:
            # Check if user has MFA enabled
            config = MFAConfiguration.objects.filter(user=user).first()
            if not config or not config.is_enabled:
                return {'success': True, 'mfa_required': False}
            
            # Check for rate limiting
            if self.is_rate_limited(user):
                return {
                    'success': False,
                    'error': 'Too many attempts. Please try again later.',
                    'locked_until': self.get_lockout_end_time(user)
                }
            
            # Create challenge record
            challenge = MFAChallenge.objects.create(
                user=user,
                challenge_type=challenge_type,
                challenge_code=token,
                ip_address=ip_address or '0.0.0.0',
                user_agent=user_agent or 'Unknown'
            )
            
            # Try TOTP devices first
            devices = MFADevice.objects.filter(
                user=user,
                is_active=True,
                device_type='totp'
            )
            
            for device in devices:
                if device.verify_token(token):
                    device.last_used_at = timezone.now()
                    device.save()
                    
                    challenge.is_successful = True
                    challenge.completed_at = timezone.now()
                    challenge.save()
                    
                    self.clear_rate_limit(user)
                    
                    return {
                        'success': True,
                        'device_used': device.device_name,
                        'mfa_required': True
                    }
            
            # Try backup codes
            backup_code = BackupCode.objects.filter(
                user=user,
                code=token,
                is_used=False
            ).first()
            
            if backup_code:
                backup_code.use_code()
                
                challenge.is_successful = True
                challenge.completed_at = timezone.now()
                challenge.save()
                
                self.clear_rate_limit(user)
                
                # Check remaining backup codes
                remaining_codes = BackupCode.objects.filter(
                    user=user,
                    is_used=False
                ).count()
                
                return {
                    'success': True,
                    'backup_code_used': True,
                    'remaining_backup_codes': remaining_codes,
                    'mfa_required': True
                }
            
            # Failed verification
            challenge.attempts += 1
            challenge.save()
            
            self.increment_rate_limit(user)
            
            return {
                'success': False,
                'error': 'Invalid verification code',
                'attempts_remaining': self.get_remaining_attempts(user)
            }
            
        except Exception as e:
            logger.error(f"Error verifying MFA: {str(e)}")
            return {
                'success': False,
                'error': 'MFA verification failed'
            }
    
    def generate_qr_code(self, provisioning_uri: str) -> str:
        """
        Generate QR code for MFA setup
        """
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        
        return base64.b64encode(buf.getvalue()).decode()
    
    def trust_device(self, user: User, device_info: Dict[str, Any]) -> TrustedDevice:
        """
        Mark a device as trusted
        """
        try:
            trust_token = TrustedDevice.create_trust_token()
            
            config = MFAConfiguration.objects.get(user=user)
            expires_at = timezone.now() + timedelta(days=config.trusted_device_duration)
            
            device = TrustedDevice.objects.create(
                user=user,
                device_id=device_info.get('device_id'),
                device_name=device_info.get('device_name', 'Unknown Device'),
                device_type=device_info.get('device_type', 'desktop'),
                browser=device_info.get('browser', 'Unknown'),
                os=device_info.get('os', 'Unknown'),
                ip_address=device_info.get('ip_address', '0.0.0.0'),
                location=device_info.get('location', ''),
                trust_token=trust_token,
                expires_at=expires_at
            )
            
            return device
            
        except Exception as e:
            logger.error(f"Error trusting device: {str(e)}")
            raise
    
    def check_trusted_device(self, user: User, trust_token: str) -> bool:
        """
        Check if device is trusted
        """
        try:
            device = TrustedDevice.objects.filter(
                user=user,
                trust_token=trust_token,
                is_active=True
            ).first()
            
            if device and device.is_valid():
                device.renew()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking trusted device: {str(e)}")
            return False
    
    def regenerate_backup_codes(self, user: User) -> List[str]:
        """
        Regenerate backup codes for user
        """
        try:
            # Invalidate old codes
            BackupCode.objects.filter(user=user, is_used=False).update(is_used=True)
            
            # Generate new codes
            config = MFAConfiguration.objects.get(user=user)
            codes = BackupCode.generate_codes_for_user(user, config.backup_codes_count)
            
            return codes
            
        except Exception as e:
            logger.error(f"Error regenerating backup codes: {str(e)}")
            raise
    
    def disable_mfa(self, user: User) -> bool:
        """
        Disable MFA for a user
        """
        try:
            # Disable all devices
            MFADevice.objects.filter(user=user).update(is_active=False)
            
            # Disable configuration
            config = MFAConfiguration.objects.filter(user=user).first()
            if config:
                config.is_enabled = False
                config.save()
            
            # Invalidate backup codes
            BackupCode.objects.filter(user=user, is_used=False).update(is_used=True)
            
            # Remove trusted devices
            TrustedDevice.objects.filter(user=user).update(is_active=False)
            
            return True
            
        except Exception as e:
            logger.error(f"Error disabling MFA: {str(e)}")
            return False
    
    # Rate limiting methods
    def is_rate_limited(self, user: User) -> bool:
        """Check if user is rate limited"""
        key = f"mfa_attempts_{user.id}"
        attempts = cache.get(key, 0)
        config = MFAConfiguration.objects.filter(user=user).first()
        max_attempts = config.max_attempts if config else 3
        return attempts >= max_attempts
    
    def increment_rate_limit(self, user: User) -> None:
        """Increment rate limit counter"""
        key = f"mfa_attempts_{user.id}"
        attempts = cache.get(key, 0)
        config = MFAConfiguration.objects.filter(user=user).first()
        lockout_duration = config.lockout_duration if config else 300
        cache.set(key, attempts + 1, lockout_duration)
    
    def clear_rate_limit(self, user: User) -> None:
        """Clear rate limit for user"""
        key = f"mfa_attempts_{user.id}"
        cache.delete(key)
    
    def get_remaining_attempts(self, user: User) -> int:
        """Get remaining MFA attempts"""
        key = f"mfa_attempts_{user.id}"
        attempts = cache.get(key, 0)
        config = MFAConfiguration.objects.filter(user=user).first()
        max_attempts = config.max_attempts if config else 3
        return max(0, max_attempts - attempts)
    
    def get_lockout_end_time(self, user: User) -> Optional[timezone.datetime]:
        """Get lockout end time"""
        if self.is_rate_limited(user):
            config = MFAConfiguration.objects.filter(user=user).first()
            lockout_duration = config.lockout_duration if config else 300
            return timezone.now() + timedelta(seconds=lockout_duration)
        return None