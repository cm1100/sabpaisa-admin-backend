"""
Client Repository - Following Repository Pattern and SOLID Principles
Dependency Inversion: Depends on interfaces, not concrete implementations
"""
from typing import Optional, List, Dict, Any
from django.db.models import Q, Count, Sum
from core.base.repository import AggregateRepository
from .models import ClientDataTable, ClientPaymentMode, ClientFeeBearer


class ClientRepository(AggregateRepository[ClientDataTable]):
    """
    Client repository with custom queries
    Single Responsibility: Data access for clients only
    Open/Closed: Extends base repository without modifying it
    """
    
    def __init__(self):
        super().__init__(ClientDataTable)
    
    def get_queryset(self):
        """Override to add default filters if needed"""
        return super().get_queryset()
    
    def find_by_client_code(self, client_code: str) -> Optional[ClientDataTable]:
        """Find client by unique client code"""
        return self.find_one_by_field('client_code', client_code)
    
    def find_active_clients(self) -> List[ClientDataTable]:
        """Get all active clients"""
        return self.find_by_field('active', True)
    
    def find_by_type(self, client_type: str) -> List[ClientDataTable]:
        """Find clients by type"""
        return self.find_by_field('client_type', client_type)
    
    def find_by_risk_category(self, risk_category: int) -> List[ClientDataTable]:
        """Find clients by risk category"""
        return self.find_by_field('risk_category', risk_category)
    
    def search_clients(self, query: str) -> List[ClientDataTable]:
        """
        Search clients by name, code, email, or contact
        Interface Segregation: Specific search method for clients
        """
        return self.search(query, ['client_name', 'client_code', 'client_email', 'client_contact'])
    
    def get_client_statistics(self) -> Dict[str, Any]:
        """
        Get aggregated client statistics
        Single Responsibility: Only aggregation logic
        """
        total = self.count()
        active = self.count({'active': True})
        by_type = self.group_by('client_type', {'count': Count('client_id')})
        by_risk = self.group_by('risk_category', {'count': Count('client_id')})
        
        return {
            'total_clients': total,
            'active_clients': active,
            'inactive_clients': total - active,
            'by_type': by_type,
            'by_risk_category': by_risk
        }
    
    def bulk_activate(self, client_ids: List[int]) -> int:
        """Bulk activate clients"""
        return self.get_queryset().filter(
            client_id__in=client_ids
        ).update(active=True)
    
    def bulk_deactivate(self, client_ids: List[int]) -> int:
        """Bulk deactivate clients"""
        return self.get_queryset().filter(
            client_id__in=client_ids
        ).update(active=False)


class ClientPaymentModeRepository(AggregateRepository[ClientPaymentMode]):
    """
    Payment mode repository
    Single Responsibility: Handles payment mode data access only
    """
    
    def __init__(self):
        super().__init__(ClientPaymentMode)
    
    def get_client_payment_modes(self, client_id: int) -> List[ClientPaymentMode]:
        """Get all payment modes for a client"""
        return self.find_by_field('client_id', client_id)
    
    def get_enabled_payment_modes(self, client_id: int) -> List[ClientPaymentMode]:
        """Get enabled payment modes for a client"""
        return list(self.get_queryset().filter(
            client_id=client_id,
            enable=True
        ))
    
    def enable_payment_mode(self, client_id: int, payment_mode: str) -> bool:
        """Enable a payment mode for client"""
        updated = self.get_queryset().filter(
            client_id=client_id,
            payment_mode=payment_mode
        ).update(enable=True)
        return updated > 0
    
    def disable_payment_mode(self, client_id: int, payment_mode: str) -> bool:
        """Disable a payment mode for client"""
        updated = self.get_queryset().filter(
            client_id=client_id,
            payment_mode=payment_mode
        ).update(enable=False)
        return updated > 0


class ClientFeeBearerRepository(AggregateRepository[ClientFeeBearer]):
    """
    Fee bearer repository
    Single Responsibility: Handles fee bearer data access only
    """
    
    def __init__(self):
        super().__init__(ClientFeeBearer)
    
    def get_client_fee_bearers(self, client_code: str) -> List[ClientFeeBearer]:
        """Get all fee bearer configurations for a client"""
        return self.find_by_field('client_code', client_code)
    
    def get_fee_bearer_for_paymode(self, client_id: int, paymode: str) -> Optional[ClientFeeBearer]:
        """Get fee bearer for specific payment mode"""
        try:
            return self.get_queryset().get(
                client_id=client_id,
                paymode=paymode
            )
        except ClientFeeBearer.DoesNotExist:
            return None
    
    def update_fee_bearer(self, client_id: int, paymode: str, bearer: str) -> bool:
        """Update fee bearer for a payment mode"""
        obj, created = self.get_queryset().update_or_create(
            client_id=client_id,
            paymode=paymode,
            defaults={'bearer': bearer}
        )
        return True