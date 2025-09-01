"""
Repository Interface - Following Interface Segregation Principle (ISP)
Each interface is specific and focused
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, TypeVar, Generic
from django.db.models import QuerySet

T = TypeVar('T')


class IRepository(ABC, Generic[T]):
    """
    Base repository interface - Dependency Inversion Principle (DIP)
    High-level modules depend on this abstraction, not concrete implementations
    """
    
    @abstractmethod
    def get_by_id(self, id: Any) -> Optional[T]:
        """Get single entity by ID"""
        pass
    
    @abstractmethod
    def get_all(self, filters: Optional[Dict] = None, limit: int = 100, offset: int = 0) -> List[T]:
        """Get all entities with optional filtering and pagination"""
        pass
    
    @abstractmethod
    def create(self, data: Dict) -> T:
        """Create new entity"""
        pass
    
    @abstractmethod
    def update(self, id: Any, data: Dict) -> Optional[T]:
        """Update existing entity"""
        pass
    
    @abstractmethod
    def delete(self, id: Any) -> bool:
        """Delete entity by ID"""
        pass
    
    @abstractmethod
    def exists(self, id: Any) -> bool:
        """Check if entity exists"""
        pass


class IBulkRepository(ABC, Generic[T]):
    """
    Bulk operations interface - Interface Segregation
    Separate interface for bulk operations (not all repositories need bulk ops)
    """
    
    @abstractmethod
    def bulk_create(self, data_list: List[Dict]) -> List[T]:
        """Create multiple entities"""
        pass
    
    @abstractmethod
    def bulk_update(self, updates: List[Dict]) -> int:
        """Update multiple entities, return count of updated"""
        pass
    
    @abstractmethod
    def bulk_delete(self, ids: List[Any]) -> int:
        """Delete multiple entities, return count of deleted"""
        pass


class ISearchRepository(ABC, Generic[T]):
    """
    Search operations interface - Interface Segregation
    Separate interface for advanced search operations
    """
    
    @abstractmethod
    def search(self, query: str, fields: Optional[List[str]] = None) -> List[T]:
        """Full-text search across specified fields"""
        pass
    
    @abstractmethod
    def find_by_field(self, field: str, value: Any) -> List[T]:
        """Find entities by specific field value"""
        pass
    
    @abstractmethod
    def find_one_by_field(self, field: str, value: Any) -> Optional[T]:
        """Find single entity by field value"""
        pass


class IAggregateRepository(ABC):
    """
    Aggregation operations interface - Interface Segregation
    For repositories that need aggregation capabilities
    """
    
    @abstractmethod
    def count(self, filters: Optional[Dict] = None) -> int:
        """Count entities with optional filters"""
        pass
    
    @abstractmethod
    def sum(self, field: str, filters: Optional[Dict] = None) -> float:
        """Sum values of a field"""
        pass
    
    @abstractmethod
    def average(self, field: str, filters: Optional[Dict] = None) -> float:
        """Calculate average of a field"""
        pass
    
    @abstractmethod
    def group_by(self, field: str, aggregations: Dict) -> List[Dict]:
        """Group by field with aggregations"""
        pass