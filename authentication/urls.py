"""
Authentication URL Configuration
"""
from django.urls import path
from .views import (
    LoginView, RefreshTokenView, LogoutView,
    UserProfileView, health_check
)
from .register_view import RegisterView
from .google_auth_view import GoogleAuthView
from .mfa_views import (
    MFASetupView, MFAVerifySetupView, MFAVerifyView,
    MFADeviceListView, BackupCodesView, TrustedDevicesView,
    MFAConfigurationView, MFADisableView
)
from .mfa_login_view import MFALoginCompleteView

app_name = 'authentication'

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/google/', GoogleAuthView.as_view(), name='google_auth'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/login/mfa/', MFALoginCompleteView.as_view(), name='mfa_login_complete'),
    path('auth/refresh/', RefreshTokenView.as_view(), name='refresh'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/user/', UserProfileView.as_view(), name='user_profile'),
    path('auth/health/', health_check, name='health_check'),
    
    # MFA endpoints
    path('auth/mfa/setup/', MFASetupView.as_view(), name='mfa_setup'),
    path('auth/mfa/verify-setup/', MFAVerifySetupView.as_view(), name='mfa_verify_setup'),
    path('auth/mfa/verify/', MFAVerifyView.as_view(), name='mfa_verify'),
    path('auth/mfa/devices/', MFADeviceListView.as_view(), name='mfa_devices'),
    path('auth/mfa/devices/<int:device_id>/', MFADeviceListView.as_view(), name='mfa_device_delete'),
    path('auth/mfa/backup-codes/', BackupCodesView.as_view(), name='backup_codes'),
    path('auth/mfa/trusted-devices/', TrustedDevicesView.as_view(), name='trusted_devices'),
    path('auth/mfa/trusted-devices/<int:device_id>/', TrustedDevicesView.as_view(), name='trusted_device_revoke'),
    path('auth/mfa/configuration/', MFAConfigurationView.as_view(), name='mfa_configuration'),
    path('auth/mfa/disable/', MFADisableView.as_view(), name='mfa_disable'),
]