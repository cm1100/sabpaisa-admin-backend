# SOLID Architecture for SabPaisa Admin API

## SOLID Principles Applied

### 1. **Single Responsibility Principle (SRP)**
Each class/module has ONE reason to change

### 2. **Open/Closed Principle (OCP)**
Open for extension, closed for modification

### 3. **Liskov Substitution Principle (LSP)**
Derived classes must be substitutable for base classes

### 4. **Interface Segregation Principle (ISP)**
Many specific interfaces are better than one general interface

### 5. **Dependency Inversion Principle (DIP)**
Depend on abstractions, not concretions

## Project Structure Following SOLID

```
backend/
├── core/                           # Core utilities and base classes
│   ├── base/
│   │   ├── models.py              # Abstract base models
│   │   ├── serializers.py        # Base serializers
│   │   ├── views.py              # Base viewsets
│   │   ├── services.py           # Base service classes
│   │   └── repositories.py       # Base repository pattern
│   │
│   ├── interfaces/                # Interface definitions (ISP)
│   │   ├── auth.py               # Authentication interfaces
│   │   ├── payment.py            # Payment processing interfaces
│   │   ├── notification.py       # Notification interfaces
│   │   └── cache.py              # Cache interfaces
│   │
│   ├── exceptions/                # Custom exceptions
│   │   ├── business.py           # Business logic exceptions
│   │   ├── validation.py         # Validation exceptions
│   │   └── api.py                # API exceptions
│   │
│   └── utils/                     # Utility functions
│       ├── validators.py         # Custom validators
│       ├── decorators.py         # Custom decorators
│       └── helpers.py            # Helper functions
│
├── apps/
│   ├── authentication/            # Authentication module (SRP)
│   │   ├── models/
│   │   │   ├── user.py           # User model only
│   │   │   ├── token.py          # Token model only
│   │   │   └── session.py        # Session model only
│   │   │
│   │   ├── services/              # Business logic (SRP)
│   │   │   ├── auth_service.py   # Authentication logic
│   │   │   ├── jwt_service.py    # JWT handling
│   │   │   ├── mfa_service.py    # MFA logic
│   │   │   └── interfaces.py     # Service interfaces
│   │   │
│   │   ├── repositories/          # Data access layer (DIP)
│   │   │   ├── user_repository.py
│   │   │   └── interfaces.py
│   │   │
│   │   ├── serializers/
│   │   │   ├── login.py
│   │   │   ├── user.py
│   │   │   └── token.py
│   │   │
│   │   └── views/
│   │       ├── auth_views.py
│   │       └── user_views.py
│   │
│   ├── clients/                   # Client management (SRP)
│   │   ├── models/
│   │   │   ├── client.py
│   │   │   └── client_config.py
│   │   │
│   │   ├── services/
│   │   │   ├── client_service.py
│   │   │   ├── validation_service.py
│   │   │   └── interfaces.py
│   │   │
│   │   ├── repositories/
│   │   │   ├── client_repository.py
│   │   │   └── interfaces.py
│   │   │
│   │   └── views/
│   │       └── client_views.py
│   │
│   ├── transactions/              # Transaction management
│   │   ├── models/
│   │   ├── services/
│   │   ├── repositories/
│   │   └── views/
│   │
│   └── settlements/               # Settlement processing
│       ├── models/
│       ├── services/
│       ├── repositories/
│       └── views/
│
├── infrastructure/                # External services (DIP)
│   ├── cache/
│   │   ├── redis_cache.py       # Redis implementation
│   │   └── interfaces.py        # Cache interface
│   │
│   ├── messaging/
│   │   ├── sms_service.py       # SMS implementation
│   │   ├── email_service.py     # Email implementation
│   │   └── interfaces.py        # Messaging interface
│   │
│   └── gateway/
│       ├── payment_gateway.py   # Payment gateway integration
│       └── interfaces.py        # Gateway interface
│
└── domain/                        # Domain layer
    ├── entities/                  # Domain entities
    ├── value_objects/             # Value objects
    └── events/                    # Domain events
```

## Implementation Examples

### 1. Repository Pattern (DIP + SRP)

```python
# core/interfaces/repository.py
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

class IRepository(ABC):
    """Base repository interface"""
    
    @abstractmethod
    def get(self, id: Any) -> Optional[Any]:
        pass
    
    @abstractmethod
    def get_all(self, filters: Dict = None) -> List[Any]:
        pass
    
    @abstractmethod
    def create(self, data: Dict) -> Any:
        pass
    
    @abstractmethod
    def update(self, id: Any, data: Dict) -> Optional[Any]:
        pass
    
    @abstractmethod
    def delete(self, id: Any) -> bool:
        pass
```

### 2. Service Layer Pattern (SRP + OCP)

```python
# apps/clients/services/interfaces.py
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class IClientService(ABC):
    """Client service interface"""
    
    @abstractmethod
    def create_client(self, data: Dict) -> Any:
        pass
    
    @abstractmethod
    def validate_client_data(self, data: Dict) -> bool:
        pass
    
    @abstractmethod
    def calculate_fees(self, client_id: str, amount: float) -> float:
        pass


# apps/clients/services/client_service.py
class ClientService(IClientService):
    """Concrete implementation of client service"""
    
    def __init__(self, repository: IClientRepository, validator: IValidator):
        self.repository = repository  # DIP: Depend on abstraction
        self.validator = validator
    
    def create_client(self, data: Dict) -> Any:
        # SRP: Only handles client creation logic
        if not self.validate_client_data(data):
            raise ValidationError("Invalid client data")
        
        return self.repository.create(data)
```

### 3. Strategy Pattern for Fee Calculation (OCP + LSP)

```python
# apps/fees/strategies/interfaces.py
from abc import ABC, abstractmethod

class IFeeStrategy(ABC):
    """Fee calculation strategy interface"""
    
    @abstractmethod
    def calculate(self, amount: float) -> float:
        pass


# apps/fees/strategies/implementations.py
class PercentageFeeStrategy(IFeeStrategy):
    def __init__(self, percentage: float):
        self.percentage = percentage
    
    def calculate(self, amount: float) -> float:
        return amount * (self.percentage / 100)


class FixedFeeStrategy(IFeeStrategy):
    def __init__(self, fixed_amount: float):
        self.fixed_amount = fixed_amount
    
    def calculate(self, amount: float) -> float:
        return self.fixed_amount


class TieredFeeStrategy(IFeeStrategy):
    def __init__(self, tiers: List[Dict]):
        self.tiers = tiers
    
    def calculate(self, amount: float) -> float:
        # Complex tiered calculation
        pass
```

### 4. View Layer with Dependency Injection

```python
# apps/clients/views/client_views.py
from rest_framework import viewsets
from core.base.views import BaseViewSet

class ClientViewSet(BaseViewSet):
    """Client API views following SOLID"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # DIP: Inject dependencies
        self.service = self.get_service()
        self.repository = self.get_repository()
    
    def get_service(self):
        # Factory pattern for service creation
        from apps.clients.services import ClientService
        from apps.clients.repositories import ClientRepository
        return ClientService(ClientRepository())
    
    def create(self, request):
        # SRP: View only handles HTTP concerns
        try:
            result = self.service.create_client(request.data)
            return Response(result, status=201)
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)
```

### 5. Cache Abstraction (DIP + ISP)

```python
# core/interfaces/cache.py
from abc import ABC, abstractmethod
from typing import Any, Optional

class ICacheService(ABC):
    """Cache service interface"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, timeout: int = None) -> bool:
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        pass


# infrastructure/cache/redis_cache.py
import redis
from core.interfaces.cache import ICacheService

class RedisCacheService(ICacheService):
    """Redis implementation of cache service"""
    
    def __init__(self, connection_string: str):
        self.client = redis.from_url(connection_string)
    
    def get(self, key: str) -> Optional[Any]:
        return self.client.get(key)
    
    def set(self, key: str, value: Any, timeout: int = None) -> bool:
        return self.client.set(key, value, ex=timeout)
    
    def delete(self, key: str) -> bool:
        return self.client.delete(key) > 0
```

## Benefits of This Architecture

1. **Testability**: Each component can be tested in isolation
2. **Maintainability**: Changes in one module don't affect others
3. **Scalability**: Easy to add new features without modifying existing code
4. **Flexibility**: Can swap implementations (e.g., Redis to Memcached)
5. **Clarity**: Clear separation of concerns

## Django-Specific SOLID Patterns

### 1. Model Managers (SRP)
```python
class ClientQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)
    
    def by_tier(self, tier):
        return self.filter(tier=tier)


class ClientManager(models.Manager):
    def get_queryset(self):
        return ClientQuerySet(self.model, using=self._db)
    
    def active(self):
        return self.get_queryset().active()
```

### 2. Serializer Composition (SRP + OCP)
```python
class BaseSerializer(serializers.ModelSerializer):
    """Base serializer with common fields"""
    pass


class ClientReadSerializer(BaseSerializer):
    """Read-only serializer"""
    class Meta:
        model = Client
        fields = '__all__'
        read_only_fields = '__all__'


class ClientWriteSerializer(BaseSerializer):
    """Write serializer with validation"""
    class Meta:
        model = Client
        exclude = ['created_at', 'updated_at']
```

### 3. Permission Classes (SRP + OCP)
```python
class BasePermission(permissions.BasePermission):
    """Base permission class"""
    pass


class IsOwnerPermission(BasePermission):
    """Check if user owns the resource"""
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user


class IsSuperAdminPermission(BasePermission):
    """Check if user is super admin"""
    def has_permission(self, request, view):
        return request.user.role == 'super_admin'
```

This architecture ensures:
- **S**: Each class has a single responsibility
- **O**: Classes are open for extension via inheritance/composition
- **L**: Subclasses can replace parent classes
- **I**: Interfaces are specific and focused
- **D**: High-level modules don't depend on low-level modules