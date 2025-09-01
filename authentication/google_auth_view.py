"""
Google OAuth Authentication View
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
import uuid
import jwt
from datetime import datetime, timedelta
from django.conf import settings

User = get_user_model()


class GoogleAuthView(APIView):
    """
    Google OAuth authentication endpoint
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Handle Google OAuth authentication"""
        data = request.data
        
        # Get Google user data
        google_id = data.get('id')
        email = data.get('email')
        given_name = data.get('given_name', '')
        family_name = data.get('family_name', '')
        picture = data.get('picture', '')
        
        if not email or not google_id:
            return Response(
                {'error': 'Invalid Google authentication data'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user exists
        try:
            user = User.objects.get(email=email)
            # Update user info from Google if needed
            if given_name and not user.first_name:
                user.first_name = given_name
            if family_name and not user.last_name:
                user.last_name = family_name
            user.save()
            created = False
        except User.DoesNotExist:
            # Create new user from Google data
            username = email.split('@')[0]
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            user = User.objects.create(
                username=username,
                email=email,
                first_name=given_name,
                last_name=family_name,
                user_id=uuid.uuid4(),
                role='viewer',  # Default role for Google users
                # No password for OAuth users
            )
            # Set unusable password for OAuth users
            user.set_unusable_password()
            user.save()
            created = True
        
        # Generate JWT tokens (same as regular login)
        from authentication.services import JWTService
        jwt_service = JWTService()
        
        access_token = jwt_service.generate_access_token(user)
        refresh_token = jwt_service.generate_refresh_token(user)
        
        return Response({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': 900,
            'user': {
                'id': str(user.user_id),
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'first_name': user.first_name,
                'last_name': user.last_name
            },
            'created': created  # Indicates if new account was created
        }, status=status.HTTP_200_OK)