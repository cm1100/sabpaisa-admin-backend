"""
Service Layer Interfaces - SOLID Principles
Services contain business logic, repositories handle data access
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, TypeVar, Generic

T = TypeVar('T')


class IService(ABC, Generic[T]):
    """
    Base service interface - Single Responsibility
    Services orchestrate business logic, not data access
    """
    
    @abstractmethod
    def get(self, id: Any) -> Optional[T]:
        """Get entity with business rules applied"""
        pass
    
    @abstractmethod
    def list(self, filters: Optional[Dict] = None, user=None) -> List[T]:
        """List entities with business rules and permissions"""
        pass
    
    @abstractmethod
    def create(self, data: Dict, user=None) -> T:
        """Create entity with validation and business rules"""
        pass
    
    @abstractmethod
    def update(self, id: Any, data: Dict, user=None) -> Optional[T]:
        """Update entity with validation and business rules"""
        pass
    
    @abstractmethod
    def delete(self, id: Any, user=None) -> bool:
        """Delete entity with business rules"""
        pass


class IValidationService(ABC):
    """
    Validation service interface - Interface Segregation
    Not all services need complex validation
    """
    
    @abstractmethod
    def validate_create(self, data: Dict) -> Dict:
        """Validate data for creation, return cleaned data"""
        pass
    
    @abstractmethod
    def validate_update(self, id: Any, data: Dict) -> Dict:
        """Validate data for update, return cleaned data"""
        pass
    
    @abstractmethod
    def validate_business_rules(self, data: Dict, context: Optional[Dict] = None) -> bool:
        """Validate against business rules"""
        pass


class INotificationService(ABC):
    """
    Notification service interface - Single Responsibility
    Handle all notification logic separately
    """
    
    @abstractmethod
    def send_email(self, to: str, subject: str, body: str, template: Optional[str] = None) -> bool:
        """Send email notification"""
        pass
    
    @abstractmethod
    def send_sms(self, to: str, message: str) -> bool:
        """Send SMS notification"""
        pass
    
    @abstractmethod
    def send_push(self, user_id: str, title: str, message: str, data: Optional[Dict] = None) -> bool:
        """Send push notification"""
        pass


class ICacheService(ABC):
    """
    Cache service interface - Dependency Inversion
    Depend on abstraction, not Redis/Memcached directly
    """
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """Set value in cache with optional timeout"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        pass
    
    @abstractmethod
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        pass


class IAuthenticationService(ABC):
    """
    Authentication service interface - Open/Closed Principle
    Can be extended for different auth methods
    """
    
    @abstractmethod
    def authenticate(self, credentials: Dict) -> Optional[Any]:
        """Authenticate user with credentials"""
        pass
    
    @abstractmethod
    def create_token(self, user: Any) -> str:
        """Create authentication token"""
        pass
    
    @abstractmethod
    def verify_token(self, token: str) -> Optional[Any]:
        """Verify and decode token"""
        pass
    
    @abstractmethod
    def refresh_token(self, refresh_token: str) -> Optional[str]:
        """Refresh access token"""
        pass
    
    @abstractmethod
    def revoke_token(self, token: str) -> bool:
        """Revoke/blacklist token"""
        pass


class IPaymentService(ABC):
    """
    Payment service interface - Interface Segregation
    Specific interface for payment operations
    """
    
    @abstractmethod
    def calculate_fee(self, amount: float, payment_mode: str, client_id: str) -> float:
        """Calculate transaction fee"""
        pass
    
    @abstractmethod
    def process_settlement(self, client_id: str, date_range: Dict) -> Dict:
        """Process settlement for client"""
        pass
    
    @abstractmethod
    def validate_transaction(self, transaction_data: Dict) -> bool:
        """Validate transaction data"""
        pass
    
    @abstractmethod
    def reconcile_transactions(self, transactions: List[Dict]) -> Dict:
        """Reconcile transactions"""
        pass


class IAuditService(ABC):
    """
    Audit service interface - Single Responsibility
    Handle all audit logging separately
    """
    
    @abstractmethod
    def log_action(self, user: Any, action: str, entity: str, entity_id: Any, 
                   old_data: Optional[Dict] = None, new_data: Optional[Dict] = None) -> bool:
        """Log user action for audit trail"""
        pass
    
    @abstractmethod
    def get_audit_trail(self, entity: str, entity_id: Any) -> List[Dict]:
        """Get audit trail for entity"""
        pass
    
    @abstractmethod
    def get_user_activity(self, user_id: Any, date_range: Optional[Dict] = None) -> List[Dict]:
        """Get user activity log"""
        pass