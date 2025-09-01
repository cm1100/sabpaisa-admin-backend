"""
Payment Configuration Services
Business logic for managing client payment configurations
"""
import logging
from typing import Dict, List, Any, Optional
from django.db import transaction
from django.utils import timezone
from cryptography.fernet import Fernet
from django.conf import settings

from .payment_config_models import (
    PaymentConfiguration, PaymentMethod, ClientPaymentMethod,
    PaymentConfigurationHistory
)
from .models import ClientDataTable

logger = logging.getLogger(__name__)


class PaymentConfigurationService:
    """
    Service for managing payment configurations
    """
    
    def __init__(self):
        # Initialize encryption for sensitive data
        self.cipher = Fernet(getattr(settings, 'PAYMENT_ENCRYPTION_KEY', Fernet.generate_key()))
    
    def create_configuration(self, client_id: str, config_data: Dict[str, Any], 
                           created_by: Any) -> PaymentConfiguration:
        """
        Create payment configuration for a client
        """
        try:
            with transaction.atomic():
                client = Client.objects.get(client_id=client_id)
                
                # Encrypt sensitive data
                if 'gateway_api_key' in config_data:
                    config_data['gateway_api_key'] = self._encrypt(config_data['gateway_api_key'])
                if 'gateway_secret_key' in config_data:
                    config_data['gateway_secret_key'] = self._encrypt(config_data['gateway_secret_key'])
                if 'gateway_webhook_secret' in config_data:
                    config_data['gateway_webhook_secret'] = self._encrypt(config_data['gateway_webhook_secret'])
                
                # Create configuration
                config = PaymentConfiguration.objects.create(
                    client=client,
                    created_by=created_by,
                    **config_data
                )
                
                # Create history entry
                PaymentConfigurationHistory.objects.create(
                    config=config,
                    change_type='CREATE',
                    changed_by=created_by,
                    new_value='Configuration created'
                )
                
                # Initialize default payment methods
                self._initialize_default_methods(config)
                
                logger.info(f"Payment configuration created for client {client_id}")
                return config
                
        except Client.DoesNotExist:
            logger.error(f"Client {client_id} not found")
            raise ValueError(f"Client {client_id} not found")
        except Exception as e:
            logger.error(f"Error creating payment configuration: {str(e)}")
            raise
    
    def update_configuration(self, config_id: str, updates: Dict[str, Any], 
                           updated_by: Any) -> PaymentConfiguration:
        """
        Update payment configuration
        """
        try:
            with transaction.atomic():
                config = PaymentConfiguration.objects.select_for_update().get(config_id=config_id)
                
                # Track changes
                changes = []
                for field, new_value in updates.items():
                    if hasattr(config, field):
                        old_value = getattr(config, field)
                        if old_value != new_value:
                            # Encrypt sensitive fields
                            if field in ['gateway_api_key', 'gateway_secret_key', 'gateway_webhook_secret']:
                                new_value = self._encrypt(new_value)
                            
                            changes.append({
                                'field': field,
                                'old': old_value,
                                'new': new_value
                            })
                            setattr(config, field, new_value)
                
                if changes:
                    config.updated_by = updated_by
                    config.updated_at = timezone.now()
                    config.save()
                    
                    # Create history entries
                    for change in changes:
                        PaymentConfigurationHistory.objects.create(
                            config=config,
                            change_type='UPDATE',
                            field_name=change['field'],
                            old_value=str(change['old']),
                            new_value=str(change['new']),
                            changed_by=updated_by
                        )
                    
                    # Mark for gateway sync
                    config.sync_status = 'PENDING'
                    config.save()
                
                logger.info(f"Payment configuration {config_id} updated")
                return config
                
        except PaymentConfiguration.DoesNotExist:
            logger.error(f"Payment configuration {config_id} not found")
            raise ValueError(f"Configuration {config_id} not found")
        except Exception as e:
            logger.error(f"Error updating payment configuration: {str(e)}")
            raise
    
    def enable_payment_method(self, client_id: str, method_code: str, 
                            custom_settings: Dict[str, Any] = None) -> ClientPaymentMethod:
        """
        Enable a payment method for a client
        """
        try:
            with transaction.atomic():
                client = Client.objects.get(client_id=client_id)
                config = PaymentConfiguration.objects.get(client=client, is_active=True)
                method = PaymentMethod.objects.get(method_code=method_code, is_active=True)
                
                # Create or update client payment method
                client_method, created = ClientPaymentMethod.objects.update_or_create(
                    client=client,
                    payment_method=method,
                    config=config,
                    defaults={
                        'is_enabled': True,
                        **(custom_settings or {})
                    }
                )
                
                # Update configuration
                if not config.payment_methods:
                    config.payment_methods = {}
                
                config.payment_methods[method_code] = {
                    'enabled': True,
                    'custom_settings': custom_settings or {}
                }
                config.save()
                
                # Create history entry
                PaymentConfigurationHistory.objects.create(
                    config=config,
                    change_type='ENABLE',
                    field_name=f'payment_method_{method_code}',
                    new_value='Enabled',
                    changed_by=custom_settings.get('updated_by') if custom_settings else None
                )
                
                logger.info(f"Payment method {method_code} enabled for client {client_id}")
                return client_method
                
        except Exception as e:
            logger.error(f"Error enabling payment method: {str(e)}")
            raise
    
    def disable_payment_method(self, client_id: str, method_code: str, 
                              reason: str = None, disabled_by: Any = None) -> bool:
        """
        Disable a payment method for a client
        """
        try:
            with transaction.atomic():
                client = Client.objects.get(client_id=client_id)
                config = PaymentConfiguration.objects.get(client=client, is_active=True)
                
                # Disable client payment method
                ClientPaymentMethod.objects.filter(
                    client=client,
                    payment_method__method_code=method_code
                ).update(is_enabled=False)
                
                # Update configuration
                if config.payment_methods and method_code in config.payment_methods:
                    config.payment_methods[method_code]['enabled'] = False
                    config.save()
                
                # Create history entry
                PaymentConfigurationHistory.objects.create(
                    config=config,
                    change_type='DISABLE',
                    field_name=f'payment_method_{method_code}',
                    old_value='Enabled',
                    new_value='Disabled',
                    change_reason=reason,
                    changed_by=disabled_by
                )
                
                logger.info(f"Payment method {method_code} disabled for client {client_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error disabling payment method: {str(e)}")
            return False
    
    def sync_with_gateway(self, config_id: str) -> Dict[str, Any]:
        """
        Sync configuration with payment gateway
        """
        try:
            config = PaymentConfiguration.objects.get(config_id=config_id)
            config.sync_status = 'IN_PROGRESS'
            config.save()
            
            # Prepare gateway payload
            payload = self._prepare_gateway_payload(config)
            
            # Mock gateway sync (replace with actual gateway API call)
            # response = gateway_api.update_merchant_config(payload)
            
            # For now, simulate success
            config.sync_status = 'COMPLETED'
            config.last_synced_at = timezone.now()
            config.sync_error = ''
            config.save()
            
            logger.info(f"Configuration {config_id} synced with gateway")
            
            return {
                'success': True,
                'synced_at': config.last_synced_at,
                'status': config.sync_status
            }
            
        except Exception as e:
            logger.error(f"Error syncing with gateway: {str(e)}")
            
            if 'config' in locals():
                config.sync_status = 'FAILED'
                config.sync_error = str(e)
                config.save()
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_configuration(self, config_id: str, verified_by: Any) -> bool:
        """
        Verify payment configuration
        """
        try:
            with transaction.atomic():
                config = PaymentConfiguration.objects.get(config_id=config_id)
                
                # Perform verification checks
                if not self._validate_configuration(config):
                    return False
                
                config.is_verified = True
                config.verified_at = timezone.now()
                config.verified_by = verified_by
                config.save()
                
                # Create history entry
                PaymentConfigurationHistory.objects.create(
                    config=config,
                    change_type='VERIFY',
                    changed_by=verified_by,
                    new_value='Configuration verified'
                )
                
                logger.info(f"Configuration {config_id} verified")
                return True
                
        except Exception as e:
            logger.error(f"Error verifying configuration: {str(e)}")
            return False
    
    def get_client_payment_methods(self, client_id: str) -> List[Dict[str, Any]]:
        """
        Get all payment methods for a client
        """
        try:
            methods = ClientPaymentMethod.objects.filter(
                client__client_id=client_id,
                is_enabled=True
            ).select_related('payment_method')
            
            return [{
                'method_code': m.payment_method.method_code,
                'method_name': m.custom_display_name or m.payment_method.method_name,
                'method_type': m.payment_method.method_type,
                'min_amount': float(m.custom_min_amount or m.payment_method.min_amount),
                'max_amount': float(m.custom_max_amount or m.payment_method.max_amount),
                'fee_percentage': float(m.custom_fee_percentage or 0),
                'priority': m.display_priority,
                'icon_url': m.payment_method.icon_url,
                'success_rate': m.success_rate
            } for m in methods]
            
        except Exception as e:
            logger.error(f"Error getting client payment methods: {str(e)}")
            return []
    
    def clone_configuration(self, source_client_id: str, target_client_id: str, 
                           cloned_by: Any) -> PaymentConfiguration:
        """
        Clone payment configuration from one client to another
        """
        try:
            with transaction.atomic():
                source_config = PaymentConfiguration.objects.get(
                    client__client_id=source_client_id,
                    is_active=True
                )
                target_client = Client.objects.get(client_id=target_client_id)
                
                # Create new configuration
                new_config = PaymentConfiguration.objects.create(
                    client=target_client,
                    payment_methods=source_config.payment_methods,
                    card_enabled=source_config.card_enabled,
                    card_min_amount=source_config.card_min_amount,
                    card_max_amount=source_config.card_max_amount,
                    card_processing_fee=source_config.card_processing_fee,
                    netbanking_enabled=source_config.netbanking_enabled,
                    netbanking_banks=source_config.netbanking_banks,
                    netbanking_processing_fee=source_config.netbanking_processing_fee,
                    upi_enabled=source_config.upi_enabled,
                    upi_processing_fee=source_config.upi_processing_fee,
                    wallet_enabled=source_config.wallet_enabled,
                    wallet_providers=source_config.wallet_providers,
                    wallet_processing_fee=source_config.wallet_processing_fee,
                    daily_transaction_limit=source_config.daily_transaction_limit,
                    monthly_transaction_limit=source_config.monthly_transaction_limit,
                    max_transaction_amount=source_config.max_transaction_amount,
                    min_transaction_amount=source_config.min_transaction_amount,
                    settlement_cycle=source_config.settlement_cycle,
                    fraud_check_enabled=source_config.fraud_check_enabled,
                    risk_score_threshold=source_config.risk_score_threshold,
                    created_by=cloned_by
                )
                
                # Clone payment methods
                source_methods = ClientPaymentMethod.objects.filter(
                    client__client_id=source_client_id,
                    is_enabled=True
                )
                
                for method in source_methods:
                    ClientPaymentMethod.objects.create(
                        client=target_client,
                        payment_method=method.payment_method,
                        config=new_config,
                        is_enabled=method.is_enabled,
                        custom_fee_percentage=method.custom_fee_percentage,
                        custom_min_amount=method.custom_min_amount,
                        custom_max_amount=method.custom_max_amount,
                        display_priority=method.display_priority,
                        custom_display_name=method.custom_display_name,
                        custom_description=method.custom_description
                    )
                
                logger.info(f"Configuration cloned from {source_client_id} to {target_client_id}")
                return new_config
                
        except Exception as e:
            logger.error(f"Error cloning configuration: {str(e)}")
            raise
    
    # Helper methods
    def _encrypt(self, data: str) -> str:
        """Encrypt sensitive data"""
        if not data:
            return data
        return self.cipher.encrypt(data.encode()).decode()
    
    def _decrypt(self, data: str) -> str:
        """Decrypt sensitive data"""
        if not data:
            return data
        return self.cipher.decrypt(data.encode()).decode()
    
    def _initialize_default_methods(self, config: PaymentConfiguration) -> None:
        """Initialize default payment methods"""
        default_methods = PaymentMethod.objects.filter(is_active=True)
        
        for method in default_methods:
            ClientPaymentMethod.objects.create(
                client=config.client,
                payment_method=method,
                config=config,
                is_enabled=method.method_type in ['CARD', 'NETBANKING', 'UPI']
            )
    
    def _validate_configuration(self, config: PaymentConfiguration) -> bool:
        """Validate payment configuration"""
        # Check required fields
        if not config.gateway_merchant_id:
            return False
        
        # Check settlement details
        if config.settlement_cycle != 'T+0' and not config.settlement_account_number:
            return False
        
        # Check at least one payment method is enabled
        enabled_methods = ClientPaymentMethod.objects.filter(
            config=config,
            is_enabled=True
        ).exists()
        
        return enabled_methods
    
    def _prepare_gateway_payload(self, config: PaymentConfiguration) -> Dict[str, Any]:
        """Prepare payload for gateway sync"""
        return {
            'merchant_id': config.gateway_merchant_id,
            'api_key': self._decrypt(config.gateway_api_key),
            'payment_methods': config.payment_methods,
            'transaction_limits': {
                'daily': float(config.daily_transaction_limit),
                'monthly': float(config.monthly_transaction_limit),
                'max_amount': float(config.max_transaction_amount),
                'min_amount': float(config.min_transaction_amount)
            },
            'settlement': {
                'cycle': config.settlement_cycle,
                'account': config.settlement_account_number,
                'ifsc': config.settlement_ifsc_code
            }
        }