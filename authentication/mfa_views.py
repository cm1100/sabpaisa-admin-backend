"""
MFA API Views
Handles Multi-Factor Authentication endpoints
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.utils import timezone
import logging

from .mfa_services import MFAService
from .serializers import (
    MFASetupSerializer, MFAVerifySetupSerializer, MFAVerifySerializer,
    MFADeviceSerializer, BackupCodeSerializer, TrustedDeviceSerializer,
    MFAConfigurationSerializer
)
from .mfa_models import (
    MFADevice, BackupCode, TrustedDevice, MFAConfiguration
)

User = get_user_model()
logger = logging.getLogger(__name__)


class MFASetupView(APIView):
    """
    Setup MFA for authenticated user
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Initiate MFA setup"""
        serializer = MFASetupSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        service = MFAService()
        try:
            result = service.setup_mfa(
                user=request.user,
                device_name=serializer.validated_data.get('device_name', 'Default')
            )
            
            return Response({
                'success': True,
                'data': result
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"MFA setup error: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to setup MFA'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MFAVerifySetupView(APIView):
    """
    Verify MFA setup with initial token
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Verify MFA setup"""
        serializer = MFAVerifySetupSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        service = MFAService()
        success = service.verify_setup(
            user=request.user,
            device_id=serializer.validated_data['device_id'],
            token=serializer.validated_data['token']
        )
        
        if success:
            return Response({
                'success': True,
                'message': 'MFA setup completed successfully'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': 'Invalid verification token'
            }, status=status.HTTP_400_BAD_REQUEST)


class MFAVerifyView(APIView):
    """
    Verify MFA token during authentication
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Verify MFA token"""
        serializer = MFAVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        service = MFAService()
        
        # Get device info for trusted device
        device_info = serializer.validated_data.get('device_info', {})
        if not device_info:
            device_info = {
                'device_id': request.META.get('HTTP_X_DEVICE_ID', ''),
                'device_name': request.META.get('HTTP_USER_AGENT', 'Unknown'),
                'ip_address': self.get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')
            }
        
        result = service.verify_mfa(
            user=request.user,
            token=serializer.validated_data['token'],
            challenge_type='login',
            ip_address=device_info.get('ip_address'),
            user_agent=device_info.get('user_agent')
        )
        
        if result['success']:
            # Trust device if requested
            if serializer.validated_data.get('trust_device'):
                trusted_device = service.trust_device(request.user, device_info)
                result['trust_token'] = trusted_device.trust_token
            
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class MFADeviceListView(APIView):
    """
    List and manage MFA devices
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """List user's MFA devices"""
        devices = MFADevice.objects.filter(user=request.user, is_active=True)
        serializer = MFADeviceSerializer(devices, many=True)
        
        return Response({
            'success': True,
            'devices': serializer.data
        }, status=status.HTTP_200_OK)
    
    def delete(self, request, device_id=None):
        """Remove MFA device"""
        if not device_id:
            return Response({
                'success': False,
                'error': 'Device ID required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            device = MFADevice.objects.get(id=device_id, user=request.user)
            
            # Check if it's the only active device
            active_devices = MFADevice.objects.filter(
                user=request.user, 
                is_active=True
            ).count()
            
            if active_devices == 1:
                return Response({
                    'success': False,
                    'error': 'Cannot remove the only active MFA device'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            device.is_active = False
            device.save()
            
            return Response({
                'success': True,
                'message': 'Device removed successfully'
            }, status=status.HTTP_200_OK)
            
        except MFADevice.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Device not found'
            }, status=status.HTTP_404_NOT_FOUND)


class BackupCodesView(APIView):
    """
    Manage backup codes
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get unused backup codes count"""
        unused_codes = BackupCode.objects.filter(
            user=request.user,
            is_used=False
        ).count()
        
        return Response({
            'success': True,
            'unused_codes_count': unused_codes
        }, status=status.HTTP_200_OK)
    
    def post(self, request):
        """Regenerate backup codes"""
        service = MFAService()
        
        try:
            codes = service.regenerate_backup_codes(request.user)
            
            return Response({
                'success': True,
                'backup_codes': codes,
                'message': 'Please save these codes in a secure place'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error regenerating backup codes: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to regenerate backup codes'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TrustedDevicesView(APIView):
    """
    Manage trusted devices
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """List trusted devices"""
        devices = TrustedDevice.objects.filter(
            user=request.user,
            is_active=True,
            expires_at__gt=timezone.now()
        )
        serializer = TrustedDeviceSerializer(devices, many=True)
        
        return Response({
            'success': True,
            'devices': serializer.data
        }, status=status.HTTP_200_OK)
    
    def delete(self, request, device_id=None):
        """Revoke trusted device"""
        if not device_id:
            return Response({
                'success': False,
                'error': 'Device ID required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            device = TrustedDevice.objects.get(id=device_id, user=request.user)
            device.is_active = False
            device.save()
            
            return Response({
                'success': True,
                'message': 'Device trust revoked'
            }, status=status.HTTP_200_OK)
            
        except TrustedDevice.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Device not found'
            }, status=status.HTTP_404_NOT_FOUND)


class MFAConfigurationView(APIView):
    """
    Manage MFA configuration
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get MFA configuration"""
        config, created = MFAConfiguration.objects.get_or_create(user=request.user)
        serializer = MFAConfigurationSerializer(config)
        
        return Response({
            'success': True,
            'configuration': serializer.data
        }, status=status.HTTP_200_OK)
    
    def patch(self, request):
        """Update MFA configuration"""
        config, created = MFAConfiguration.objects.get_or_create(user=request.user)
        serializer = MFAConfigurationSerializer(config, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'configuration': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class MFADisableView(APIView):
    """
    Disable MFA for user
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Disable MFA (requires current password)"""
        password = request.data.get('password')
        if not password:
            return Response({
                'success': False,
                'error': 'Password required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify password
        if not request.user.check_password(password):
            return Response({
                'success': False,
                'error': 'Invalid password'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        service = MFAService()
        success = service.disable_mfa(request.user)
        
        if success:
            return Response({
                'success': True,
                'message': 'MFA disabled successfully'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': 'Failed to disable MFA'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)