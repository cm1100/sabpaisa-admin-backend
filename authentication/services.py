"""
Authentication Services - Following SOLID Principles
Dependency Inversion: Services depend on interfaces, not implementations
"""
import jwt
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from django.conf import settings
from django.contrib.auth import authenticate
from django.utils import timezone
from core.interfaces.service import IAuthenticationService
from .models import AdminUser, RefreshToken, LoginAttempt
from .mfa_models import MFAConfiguration
from .mfa_services import MFAService


class JWTService:
    """
    JWT token management service
    Single Responsibility: Only handles JWT operations
    """
    
    def __init__(self):
        self.secret = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_lifetime = settings.JWT_ACCESS_TOKEN_LIFETIME
        self.refresh_token_lifetime = settings.JWT_REFRESH_TOKEN_LIFETIME
    
    def generate_access_token(self, user: AdminUser) -> str:
        """Generate JWT access token"""
        payload = {
            'user_id': str(user.user_id),
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'exp': datetime.utcnow() + self.access_token_lifetime,
            'iat': datetime.utcnow(),
            'type': 'access'
        }
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)
    
    def generate_refresh_token(self, user: AdminUser) -> str:
        """Generate and store refresh token"""
        token_string = str(uuid.uuid4())
        expires_at = timezone.now() + self.refresh_token_lifetime
        
        # Store in database
        RefreshToken.objects.create(
            user=user,
            token=token_string,
            expires_at=expires_at
        )
        
        return token_string
    
    def verify_access_token(self, token: str) -> Optional[Dict]:
        """Verify and decode access token"""
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            if payload.get('type') != 'access':
                return None
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Generate new access token from refresh token"""
        try:
            token_obj = RefreshToken.objects.get(token=refresh_token)
            if not token_obj.is_valid():
                return None
            
            return self.generate_access_token(token_obj.user)
        except RefreshToken.DoesNotExist:
            return None


class AuthenticationService(IAuthenticationService):
    """
    Main authentication service
    Open/Closed Principle: Can be extended without modification
    Dependency Inversion: Depends on JWT service interface
    """
    
    def __init__(self):
        self.jwt_service = JWTService()
    
    def authenticate(self, credentials: Dict) -> Optional[Any]:
        """
        Authenticate user with credentials
        Interface Segregation: Implements only what's needed
        """
        username = credentials.get('username') or credentials.get('email')
        password = credentials.get('password')
        
        if not username or not password:
            return None
        
        # Track login attempt
        ip_address = credentials.get('ip_address', '0.0.0.0')
        
        user = authenticate(username=username, password=password)
        
        # Log attempt
        LoginAttempt.objects.create(
            username=username,
            ip_address=ip_address,
            success=user is not None,
            failure_reason=None if user else 'Invalid credentials'
        )
        
        if user:
            # Update last login info
            user.last_login_ip = ip_address
            user.save(update_fields=['last_login_ip', 'last_login'])
        
        return user
    
    def create_token(self, user: Any) -> str:
        """Create authentication token"""
        return self.jwt_service.generate_access_token(user)
    
    def verify_token(self, token: str) -> Optional[Any]:
        """Verify and decode token"""
        payload = self.jwt_service.verify_access_token(token)
        if not payload:
            return None
        
        try:
            user = AdminUser.objects.get(user_id=payload['user_id'])
            return user
        except AdminUser.DoesNotExist:
            return None
    
    def refresh_token(self, refresh_token: str) -> Optional[str]:
        """Refresh access token"""
        return self.jwt_service.refresh_access_token(refresh_token)
    
    def revoke_token(self, token: str) -> bool:
        """Revoke refresh token"""
        try:
            token_obj = RefreshToken.objects.get(token=token)
            token_obj.revoke()
            return True
        except RefreshToken.DoesNotExist:
            return False
    
    def login(self, username: str, password: str, ip_address: str = None, user_agent: str = None) -> Optional[Dict]:
        """
        Complete login flow with MFA support
        Single Responsibility: Orchestrates login process
        """
        credentials = {
            'username': username,
            'password': password,
            'ip_address': ip_address or '0.0.0.0'
        }
        
        user = self.authenticate(credentials)
        if not user:
            return None
        
        # Check if MFA is enabled
        mfa_config = MFAConfiguration.objects.filter(user=user).first()
        if mfa_config and mfa_config.is_enabled:
            # Return partial response requiring MFA
            return {
                'requires_mfa': True,
                'user_id': str(user.user_id),
                'mfa_required': True,
                'message': 'MFA verification required'
            }
        
        access_token = self.jwt_service.generate_access_token(user)
        refresh_token = self.jwt_service.generate_refresh_token(user)
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'requires_mfa': False,
            'user': {
                'id': str(user.user_id),
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
        }
    
    def complete_mfa_login(self, user_id: str, mfa_token: str, ip_address: str = None, user_agent: str = None) -> Optional[Dict]:
        """
        Complete login after MFA verification
        """
        try:
            user = AdminUser.objects.get(user_id=user_id)
            mfa_service = MFAService()
            
            # Verify MFA token
            result = mfa_service.verify_mfa(
                user=user,
                token=mfa_token,
                challenge_type='login',
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            if not result['success']:
                return None
            
            # Generate tokens on successful MFA
            access_token = self.jwt_service.generate_access_token(user)
            refresh_token = self.jwt_service.generate_refresh_token(user)
            
            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': {
                    'id': str(user.user_id),
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                    'first_name': user.first_name,
                    'last_name': user.last_name
                }
            }
        except AdminUser.DoesNotExist:
            return None
    
    def logout(self, user: AdminUser, refresh_token: str = None) -> bool:
        """
        Logout user
        Single Responsibility: Handles logout logic only
        """
        # Revoke all user's refresh tokens
        RefreshToken.objects.filter(user=user, revoked=False).update(
            revoked=True,
            revoked_at=timezone.now()
        )
        return True
    
    def get_user_from_token(self, token: str) -> Optional[AdminUser]:
        """Get user from access token"""
        return self.verify_token(token)