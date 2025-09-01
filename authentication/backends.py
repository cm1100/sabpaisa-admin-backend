"""
JWT Authentication Backend for Django REST Framework
"""
import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


User = get_user_model()


class JWTAuthentication(BaseAuthentication):
    """
    JWT Authentication Backend
    Supports Bearer token format: Authorization: Bearer <token>
    """
    
    def authenticate(self, request):
        """
        Authenticate user using JWT token from Authorization header
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not auth_header:
            return None
        
        # Check for Bearer token format
        if not auth_header.startswith('Bearer '):
            return None
        
        # Extract token
        token = auth_header.split(' ')[1]
        
        try:
            # Decode JWT token
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            # Check token type
            if payload.get('type') != 'access':
                raise AuthenticationFailed('Invalid token type')
            
            # Get user ID from payload
            user_id = payload.get('user_id')
            if not user_id:
                raise AuthenticationFailed('Token contains no user identification')
            
            # Get user from database
            try:
                user = User.objects.get(user_id=user_id)
            except User.DoesNotExist:
                raise AuthenticationFailed('User not found')
            
            if not user.is_active:
                raise AuthenticationFailed('User account is disabled')
            
            return (user, token)
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token has expired')
        except jwt.DecodeError:
            raise AuthenticationFailed('Error decoding token')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token')
    
    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a `401 Unauthenticated` response
        """
        return 'Bearer'