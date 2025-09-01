"""
MFA Login Completion View
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .services import AuthenticationService
from .serializers import LoginResponseSerializer


class MFALoginCompleteView(APIView):
    """
    Complete login with MFA verification
    """
    permission_classes = [AllowAny]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthenticationService()
    
    def post(self, request):
        """Complete login after MFA verification"""
        user_id = request.data.get('user_id')
        mfa_token = request.data.get('mfa_token')
        
        if not user_id or not mfa_token:
            return Response({
                'error': 'user_id and mfa_token are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get IP and user agent
        ip_address = request.META.get('REMOTE_ADDR', '0.0.0.0')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Complete MFA login
        result = self.auth_service.complete_mfa_login(
            user_id=user_id,
            mfa_token=mfa_token,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if not result:
            return Response({
                'error': 'Invalid MFA token'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
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