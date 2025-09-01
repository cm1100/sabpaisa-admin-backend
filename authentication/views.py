"""
Authentication Views - Following SOLID Principles
Dependency Inversion: Views depend on service interfaces
"""
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .services import AuthenticationService
from .serializers import (
    LoginSerializer, LoginResponseSerializer,
    RefreshTokenSerializer, UserSerializer,
    LogoutSerializer
)


class LoginView(APIView):
    """
    Login endpoint
    Single Responsibility: Only handles login HTTP logic
    """
    permission_classes = [AllowAny]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthenticationService()  # Dependency Injection
    
    def post(self, request):
        """Handle login request with MFA support"""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get IP address and user agent
        ip_address = request.META.get('REMOTE_ADDR', '0.0.0.0')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Attempt login
        username = serializer.validated_data.get('username') or serializer.validated_data.get('email')
        password = serializer.validated_data['password']
        
        # If username contains @ symbol, try to find the user by email
        if '@' in username:
            from authentication.models import AdminUser
            try:
                user = AdminUser.objects.get(email=username)
                username = user.username
            except AdminUser.DoesNotExist:
                pass  # Let it fail with the original username
        
        result = self.auth_service.login(username, password, ip_address, user_agent)
        
        if not result:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Check if MFA is required
        if result.get('requires_mfa'):
            return Response({
                'requires_mfa': True,
                'user_id': result['user_id'],
                'message': 'Please provide MFA verification code'
            }, status=status.HTTP_200_OK)
        
        # Return tokens and user info
        response_serializer = LoginResponseSerializer(data={
            'access_token': result['access_token'],
            'refresh_token': result['refresh_token'],
            'token_type': 'Bearer',
            'expires_in': 900,
            'user': result['user']
        })
        response_serializer.is_valid()
        
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class RefreshTokenView(APIView):
    """
    Refresh token endpoint
    Open/Closed: Can be extended without modification
    """
    permission_classes = [AllowAny]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthenticationService()
    
    def post(self, request):
        """Refresh access token"""
        serializer = RefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        refresh_token = serializer.validated_data['refresh_token']
        new_access_token = self.auth_service.refresh_token(refresh_token)
        
        if not new_access_token:
            return Response(
                {'error': 'Invalid or expired refresh token'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        return Response({
            'access_token': new_access_token,
            'token_type': 'Bearer',
            'expires_in': 900
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    Logout endpoint
    Interface Segregation: Specific view for logout
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthenticationService()
    
    def post(self, request):
        """Handle logout"""
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        refresh_token = serializer.validated_data.get('refresh_token')
        
        # Logout user
        self.auth_service.logout(request.user, refresh_token)
        
        return Response(
            {'message': 'Successfully logged out'},
            status=status.HTTP_200_OK
        )


class UserProfileView(APIView):
    """
    User profile endpoint
    Liskov Substitution: Can be replaced with any APIView
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get current user profile"""
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def patch(self, request):
        """Update user profile"""
        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint
    Single Responsibility: Only checks auth service health
    """
    return Response({
        'status': 'healthy',
        'service': 'authentication',
        'timestamp': timezone.now().isoformat()
    }, status=status.HTTP_200_OK)