"""
Base Repository Implementation - Single Responsibility Principle (SRP)
Each repository class has one reason to change: its data access logic
"""
from typing import Optional, List, Dict, Any, Type, TypeVar, Generic
from django.db.models import Model, QuerySet, Q, Sum, Avg, Count
from django.core.exceptions import ObjectDoesNotExist
from core.interfaces.repository import (
    IRepository, IBulkRepository, ISearchRepository, IAggregateRepository
)

T = TypeVar('T', bound=Model)


class BaseRepository(IRepository[T], Generic[T]):
    """
    Base repository with common CRUD operations
    Open/Closed Principle - Open for extension, closed for modification
    """
    
    def __init__(self, model: Type[T]):
        """
        Dependency Injection - model is injected, not hardcoded
        """
        self.model = model
        
    def get_queryset(self) -> QuerySet[T]:
        """
        Template Method Pattern - subclasses can override to add default filters
        """
        return self.model.objects.all()
    
    def get_by_id(self, id: Any) -> Optional[T]:
        """Get single entity by ID"""
        try:
            return self.get_queryset().get(pk=id)
        except ObjectDoesNotExist:
            return None
    
    def get_all(self, filters: Optional[Dict] = None, limit: int = 100, offset: int = 0) -> List[T]:
        """Get all entities with optional filtering and pagination"""
        queryset = self.get_queryset()
        
        if filters:
            queryset = queryset.filter(**filters)
        
        return list(queryset[offset:offset + limit])
    
    def create(self, data: Dict) -> T:
        """Create new entity"""
        return self.model.objects.create(**data)
    
    def update(self, id: Any, data: Dict) -> Optional[T]:
        """Update existing entity using Django ORM best practices"""
        # For unmanaged models, use update() instead of save()
        updated_count = self.get_queryset().filter(pk=id).update(**data)
        
        if updated_count > 0:
            # Return the updated entity
            return self.get_by_id(id)
        
        return None
    
    def delete(self, id: Any) -> bool:
        """Delete entity by ID"""
        entity = self.get_by_id(id)
        if entity:
            entity.delete()
            return True
        return False
    
    def exists(self, id: Any) -> bool:
        """Check if entity exists"""
        return self.get_queryset().filter(pk=id).exists()


class BulkRepository(BaseRepository[T], IBulkRepository[T], Generic[T]):
    """
    Repository with bulk operations support
    Liskov Substitution - Can be used wherever BaseRepository is expected
    """
    
    def bulk_create(self, data_list: List[Dict]) -> List[T]:
        """Create multiple entities efficiently"""
        entities = [self.model(**data) for data in data_list]
        return self.model.objects.bulk_create(entities)
    
    def bulk_update(self, updates: List[Dict]) -> int:
        """Update multiple entities"""
        count = 0
        for update in updates:
            id = update.pop('id')
            if self.update(id, update):
                count += 1
        return count
    
    def bulk_delete(self, ids: List[Any]) -> int:
        """Delete multiple entities"""
        return self.get_queryset().filter(pk__in=ids).delete()[0]


class SearchRepository(BulkRepository[T], ISearchRepository[T], Generic[T]):
    """
    Repository with search capabilities
    Interface Segregation - Only repos needing search inherit this
    """
    
    def search(self, query: str, fields: Optional[List[str]] = None) -> List[T]:
        """Full-text search across specified fields"""
        if not fields:
            # Default to searching in 'name' field if exists
            fields = ['name'] if hasattr(self.model, 'name') else []
        
        q_objects = Q()
        for field in fields:
            q_objects |= Q(**{f"{field}__icontains": query})
        
        return list(self.get_queryset().filter(q_objects))
    
    def find_by_field(self, field: str, value: Any) -> List[T]:
        """Find entities by specific field value"""
        return list(self.get_queryset().filter(**{field: value}))
    
    def find_one_by_field(self, field: str, value: Any) -> Optional[T]:
        """Find single entity by field value"""
        try:
            return self.get_queryset().get(**{field: value})
        except ObjectDoesNotExist:
            return None
        except self.model.MultipleObjectsReturned:
            # Return first if multiple found
            return self.get_queryset().filter(**{field: value}).first()


class AggregateRepository(SearchRepository[T], IAggregateRepository, Generic[T]):
    """
    Repository with aggregation capabilities
    Single Responsibility - Only handles aggregation logic
    """
    
    def count(self, filters: Optional[Dict] = None) -> int:
        """Count entities with optional filters"""
        queryset = self.get_queryset()
        if filters:
            queryset = queryset.filter(**filters)
        return queryset.count()
    
    def sum(self, field: str, filters: Optional[Dict] = None) -> float:
        """Sum values of a field"""
        queryset = self.get_queryset()
        if filters:
            queryset = queryset.filter(**filters)
        result = queryset.aggregate(total=Sum(field))
        return result['total'] or 0.0
    
    def average(self, field: str, filters: Optional[Dict] = None) -> float:
        """Calculate average of a field"""
        queryset = self.get_queryset()
        if filters:
            queryset = queryset.filter(**filters)
        result = queryset.aggregate(avg=Avg(field))
        return result['avg'] or 0.0
    
    def group_by(self, field: str, aggregations: Dict) -> List[Dict]:
        """
        Group by field with aggregations
        Example: group_by('status', {'count': Count('id'), 'total': Sum('amount')})
        """
        return list(
            self.get_queryset()
            .values(field)
            .annotate(**aggregations)
            .order_by(field)
        )