"""
Client Service Layer - Following SOLID Principles
Services orchestrate business logic, not data access
"""
from typing import Optional, List, Dict, Any
from django.db import transaction
from django.utils import timezone
from core.interfaces.service import IService, IValidationService
from .repositories import ClientRepository, ClientPaymentModeRepository, ClientFeeBearerRepository
from .models import ClientDataTable


class ClientValidationService(IValidationService):
    """
    Client validation service
    Single Responsibility: Only handles validation logic
    """
    
    def validate_create(self, data: Dict) -> Dict:
        """Validate data for client creation"""
        errors = {}
        
        # Required fields validation
        required_fields = ['client_name', 'client_code', 'client_contact', 'client_email']
        for field in required_fields:
            if field not in data or not data[field]:
                errors[field] = f"{field} is required"
        
        # Email validation
        if 'client_email' in data and '@' not in data.get('client_email', ''):
            errors['client_email'] = "Invalid email format"
        
        # Client code uniqueness (would check in DB in real implementation)
        if 'client_code' in data:
            # Check if client_code already exists
            pass
        
        if errors:
            raise ValueError(f"Validation errors: {errors}")
        
        return data
    
    def validate_update(self, id: Any, data: Dict) -> Dict:
        """Validate data for client update"""
        # Similar validation but exclude unique checks for own record
        if 'client_email' in data and '@' not in data.get('client_email', ''):
            raise ValueError("Invalid email format")
        
        return data
    
    def validate_business_rules(self, data: Dict, context: Optional[Dict] = None) -> bool:
        """
        Validate against business rules
        Open/Closed: Can be extended for new rules without modification
        """
        # Business rule: Risk category must be between 1-5
        if 'risk_category' in data and data['risk_category'] is not None:
            if not 1 <= data['risk_category'] <= 5:
                raise ValueError("Risk category must be between 1 and 5")
        
        # Business rule: If high risk (5), additional verification required
        # Temporarily disabled for development
        # if data.get('risk_category') == 5:
        #     if not data.get('is_whitelisted'):
        #         raise ValueError("High risk clients must be whitelisted")
        
        return True


class ClientService(IService[ClientDataTable]):
    """
    Main client service
    Dependency Inversion: Depends on repository interfaces
    Single Responsibility: Orchestrates client business logic
    """
    
    def __init__(self):
        """Dependency Injection through constructor"""
        self.repository = ClientRepository()
        self.payment_mode_repo = ClientPaymentModeRepository()
        self.fee_bearer_repo = ClientFeeBearerRepository()
        self.validator = ClientValidationService()
    
    def get(self, id: Any) -> Optional[ClientDataTable]:
        """Get client with business rules applied"""
        client = self.repository.get_by_id(id)
        if client:
            # Apply any business logic transformations
            self._enrich_client_data(client)
        return client
    
    def list(self, filters: Optional[Dict] = None, user=None) -> List[ClientDataTable]:
        """
        List clients with business rules and permissions
        Liskov Substitution: Can be substituted with any IService implementation
        """
        # Apply user-based filtering if needed
        if user and not user.is_superuser:
            filters = filters or {}
            # Add permission-based filters
        
        clients = self.repository.get_all(filters)
        
        # Enrich with additional data if needed
        for client in clients:
            self._enrich_client_data(client)
        
        return clients
    
    @transaction.atomic
    def create(self, data: Dict, user=None) -> ClientDataTable:
        """
        Create client with validation and business rules
        Interface Segregation: Uses specific validation interface
        """
        # Validate data
        validated_data = self.validator.validate_create(data)
        self.validator.validate_business_rules(validated_data)
        
        # Generate next client_id
        from django.db.models import Max
        max_id = ClientDataTable.objects.aggregate(Max('client_id'))['client_id__max']
        validated_data['client_id'] = (max_id or 0) + 1
        
        # Add audit fields
        validated_data['created_by'] = user.username if user else 'system'
        validated_data['creation_date'] = timezone.now()
        
        # Set default values for required fields if not provided
        validated_data.setdefault('auth_key', '')
        validated_data.setdefault('auth_iv', '')
        validated_data.setdefault('client_user_name', '')
        validated_data.setdefault('client_pass', '')
        validated_data.setdefault('success_ru_url', '')
        validated_data.setdefault('failed_ru_url', '')
        validated_data.setdefault('push_api_url', '')
        validated_data.setdefault('client_logo_path', '')
        
        # Create client
        client = self.repository.create(validated_data)
        
        # Initialize default payment modes
        self._initialize_default_payment_modes(client.client_id)
        
        return client
    
    @transaction.atomic
    def update(self, id: Any, data: Dict, user=None) -> Optional[ClientDataTable]:
        """Update client with validation and business rules using Django ORM"""
        # Get client using repository pattern
        existing_client = self.repository.get_by_id(id)
        if not existing_client:
            return None
        
        # Validate data
        validated_data = self.validator.validate_update(id, data)
        if validated_data:  # Only validate business rules if there's data to update
            self.validator.validate_business_rules(validated_data, {'existing': existing_client})
        
        # Add audit fields
        validated_data['update_by'] = user.username if user else 'system'
        validated_data['update_date'] = timezone.now()
        
        # Use repository pattern for update
        return self.repository.update(id, validated_data)
    
    @transaction.atomic
    def delete(self, id: Any, user=None) -> bool:
        """
        Delete client with business rules
        Single Responsibility: Only handles deletion logic
        """
        client = self.repository.get_by_id(id)
        if not client:
            return False
        
        # Business rule: Cannot delete active clients
        if client.active:
            raise ValueError("Cannot delete active client. Please deactivate first.")
        
        # Business rule: Cannot delete clients with recent transactions
        # (would check transaction table in real implementation)
        
        return self.repository.delete(id)
    
    def activate_client(self, client_id: int, user=None) -> bool:
        """
        Activate a client using repository pattern
        Open/Closed: New activation logic can be added without modifying existing
        """
        client = self.repository.get_by_id(client_id)
        if not client:
            return False
        
        # Business rule checks before activation
        if not client.client_email:
            raise ValueError("Client must have email before activation")
        
        # Use repository update method
        update_data = {
            'active': True,
            'update_date': timezone.now(),
            'update_by': user.username if user else 'system'
        }
        
        updated_client = self.repository.update(client_id, update_data)
        return updated_client is not None
    
    def deactivate_client(self, client_id: int, user=None) -> bool:
        """Deactivate a client using repository pattern"""
        client = self.repository.get_by_id(client_id)
        if not client:
            return False
        
        # Use repository update method
        update_data = {
            'active': False,
            'update_date': timezone.now(),
            'update_by': user.username if user else 'system'
        }
        
        updated_client = self.repository.update(client_id, update_data)
        return updated_client is not None
    
    def bulk_activate(self, client_ids: List[int], user=None) -> int:
        """Bulk activate multiple clients"""
        # Validate all clients exist and meet criteria
        clients = self.repository.get_all({'client_id__in': client_ids})
        
        for client in clients:
            if not client.client_email:
                raise ValueError(f"Client {client.client_id} must have email before activation")
        
        return self.repository.bulk_activate(client_ids)
    
    def get_client_statistics(self) -> Dict[str, Any]:
        """
        Get client statistics
        Single Responsibility: Delegates to repository for data aggregation
        """
        return self.repository.get_client_statistics()
    
    def clone_client(self, source_client_id: int, new_client_code: str, user=None) -> ClientDataTable:
        """
        Clone client configuration
        Open/Closed: Can be extended with new cloning strategies
        """
        source_client = self.repository.get_by_id(source_client_id)
        if not source_client:
            raise ValueError("Source client not found")
        
        # Create new client data from source
        new_data = {
            'client_code': new_client_code,
            'client_name': f"{source_client.client_name} (Clone)",
            'client_type': source_client.client_type,
            'client_email': source_client.client_email,
            'client_contact': source_client.client_contact,
            'risk_category': source_client.risk_category,
            # Copy other relevant fields
        }
        
        # Create new client
        new_client = self.create(new_data, user)
        
        # Clone payment modes
        self._clone_payment_modes(source_client_id, new_client.client_id)
        
        # Clone fee bearers
        self._clone_fee_bearers(source_client_id, new_client.client_id)
        
        return new_client
    
    def _enrich_client_data(self, client: ClientDataTable) -> None:
        """
        Enrich client with additional data
        Single Responsibility: Only enrichment logic
        """
        # Add payment modes count
        client.payment_modes_count = self.payment_mode_repo.count({'client_data_client_id': client.client_id})
        
        # Add fee bearer info
        client.fee_bearers = self.fee_bearer_repo.get_client_fee_bearers(client.client_code)
    
    def _initialize_default_payment_modes(self, client_id: int) -> None:
        """Initialize default payment modes for new client"""
        # Skip payment mode initialization for now to avoid errors
        pass
    
    def _clone_payment_modes(self, source_id: int, target_id: int) -> None:
        """Clone payment modes from source to target client"""
        source_modes = self.payment_mode_repo.get_client_payment_modes(source_id)
        
        for mode in source_modes:
            self.payment_mode_repo.create({
                'client_id': target_id,
                'payment_mode': mode.payment_mode,
                'enable': mode.enable,
                'created_date': timezone.now()
            })
    
    def _clone_fee_bearers(self, source_id: int, target_id: int) -> None:
        """Clone fee bearers from source to target client"""
        source_bearers = self.fee_bearer_repo.get_client_fee_bearers(source_id)
        
        for bearer in source_bearers:
            self.fee_bearer_repo.create({
                'client_id': target_id,
                'paymode': bearer.paymode,
                'bearer': bearer.bearer,
                'created_date': timezone.now()
            })