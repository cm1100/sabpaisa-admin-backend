"""
Transaction Interfaces - SOLID Principles Implementation
Following Interface Segregation and Dependency Inversion principles
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from decimal import Decimal


class ITransactionRepository(ABC):
    """
    Interface for transaction data access
    """
    
    @abstractmethod
    def get_by_id(self, txn_id: str) -> Optional[Any]:
        """Get transaction by ID"""
        pass
    
    @abstractmethod
    def get_filtered_queryset(self, filters: Dict[str, Any]) -> Any:
        """Get filtered queryset based on criteria"""
        pass
    
    @abstractmethod
    def get_aggregates(self, queryset: Any) -> Dict[str, Any]:
        """Get aggregated data from queryset"""
        pass
    
    @abstractmethod
    def bulk_update_settlement_status(self, txn_ids: List[str], status: str) -> int:
        """Bulk update settlement status"""
        pass


class ITransactionService(ABC):
    """
    Interface for transaction business logic
    """
    
    @abstractmethod
    def get_transactions(
        self, 
        filters: Dict[str, Any], 
        page: int = 1, 
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Get paginated transactions with filters"""
        pass
    
    @abstractmethod
    def get_transaction_by_id(self, txn_id: str) -> Optional[Dict[str, Any]]:
        """Get single transaction details"""
        pass
    
    @abstractmethod
    def get_transaction_stats(self, date_range: str = '24h') -> Dict[str, Any]:
        """Get transaction statistics for dashboard"""
        pass


class IRefundService(ABC):
    """
    Interface for refund operations
    """
    
    @abstractmethod
    def initiate_refund(
        self, 
        txn_id: str, 
        amount: Decimal, 
        reason: str, 
        user: Any
    ) -> Any:
        """Initiate a refund request"""
        pass
    
    @abstractmethod
    def approve_refund(self, refund_id: int, approver: Any) -> Any:
        """Approve a refund request"""
        pass
    
    @abstractmethod
    def reject_refund(self, refund_id: int, reason: str) -> Any:
        """Reject a refund request"""
        pass
    
    @abstractmethod
    def get_refunds(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get list of refunds with filters"""
        pass


class ISettlementService(ABC):
    """
    Interface for settlement operations
    """
    
    @abstractmethod
    def get_pending_settlements(self, client_id: Optional[str] = None) -> Any:
        """Get pending settlements"""
        pass
    
    @abstractmethod
    def process_settlement_batch(self, txn_ids: List[str]) -> Dict[str, Any]:
        """Process batch settlement"""
        pass


class IAnalyticsService(ABC):
    """
    Interface for analytics operations
    """
    
    @abstractmethod
    def get_payment_mode_distribution(self, date_range: str = '7d') -> List[Dict[str, Any]]:
        """Get payment mode distribution"""
        pass
    
    @abstractmethod
    def get_hourly_transaction_volume(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get hourly transaction volume"""
        pass
    
    @abstractmethod
    def get_top_clients_by_volume(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top clients by transaction volume"""
        pass


class IPaymentGatewayAdapter(ABC):
    """
    Interface for payment gateway integration
    Adapter pattern for different payment gateways
    """
    
    @abstractmethod
    def initiate_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Initiate payment with gateway"""
        pass
    
    @abstractmethod
    def check_payment_status(self, transaction_id: str) -> Dict[str, Any]:
        """Check payment status"""
        pass
    
    @abstractmethod
    def process_refund(self, refund_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process refund with gateway"""
        pass
    
    @abstractmethod
    def validate_webhook(self, webhook_data: Dict[str, Any]) -> bool:
        """Validate webhook from gateway"""
        pass