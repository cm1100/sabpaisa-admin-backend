"""
Transaction Services - Following SOLID Principles & Clean Architecture
Service Layer: Business logic separated from views and models
Repository Pattern: Data access abstraction
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
from django.db.models import Q, Sum, Count, Avg, F
from django.db import transaction as db_transaction
from django.core.paginator import Paginator
from django.utils import timezone
from django.core.cache import cache
import logging

from .models import (
    TransactionDetail, 
    SettledTransactions,
    TransactionReconTable,
    RefundRequestFromClient
)
from .interfaces import (
    ITransactionRepository,
    ITransactionService,
    IRefundService,
    ISettlementService,
    IAnalyticsService
)

logger = logging.getLogger(__name__)


class TransactionRepository(ITransactionRepository):
    """
    Repository for transaction data access
    Single Responsibility: Data access layer for transactions
    """
    
    def get_by_id(self, txn_id: str) -> Optional[TransactionDetail]:
        """Get transaction by ID"""
        try:
            return TransactionDetail.objects.get(txn_id=txn_id)
        except TransactionDetail.DoesNotExist:
            return None
    
    def get_filtered_queryset(self, filters: Dict[str, Any]) -> Any:
        """Get filtered queryset based on criteria"""
        queryset = TransactionDetail.objects.all()
        
        # Apply filters
        if filters.get('status'):
            queryset = queryset.filter(status__iexact=filters['status'])
        
        if filters.get('client_code'):
            queryset = queryset.filter(client_code=filters['client_code'])
        
        if filters.get('payment_mode'):
            queryset = queryset.filter(payment_mode=filters['payment_mode'])
        
        if filters.get('date_from'):
            queryset = queryset.filter(trans_date__gte=filters['date_from'])
        
        if filters.get('date_to'):
            queryset = queryset.filter(trans_date__lte=filters['date_to'])
        
        if filters.get('min_amount'):
            queryset = queryset.filter(paid_amount__gte=filters['min_amount'])
        
        if filters.get('max_amount'):
            queryset = queryset.filter(paid_amount__lte=filters['max_amount'])
        
        if filters.get('is_settled') is not None:
            queryset = queryset.filter(is_settled=filters['is_settled'])
        
        if filters.get('search'):
            search_term = filters['search']
            queryset = queryset.filter(
                Q(txn_id__icontains=search_term) |
                Q(payee_email__icontains=search_term) |
                Q(payee_mob__icontains=search_term) |
                Q(payee_first_name__icontains=search_term) |
                Q(payee_lst_name__icontains=search_term)
            )
        
        return queryset
    
    def get_aggregates(self, queryset: Any) -> Dict[str, Any]:
        """Get aggregated data from queryset"""
        return queryset.aggregate(
            total_amount=Sum('paid_amount'),
            total_transactions=Count('txn_id'),
            avg_amount=Avg('paid_amount'),
            total_fees=Sum(F('convcharges') + F('ep_charges') + F('gst'))
        )
    
    def bulk_update_settlement_status(self, txn_ids: List[str], status: str) -> int:
        """Bulk update settlement status"""
        return TransactionDetail.objects.filter(
            txn_id__in=txn_ids
        ).update(
            is_settled=True,
            settlement_status=status,
            settlement_date=timezone.now()
        )


class TransactionService(ITransactionService):
    """
    Main transaction service implementing business logic
    Open/Closed Principle: Open for extension, closed for modification
    """
    
    def __init__(self):
        self.repository = TransactionRepository()
    
    def get_transactions(
        self, 
        filters: Dict[str, Any], 
        page: int = 1, 
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Get paginated transactions with filters"""
        try:
            # Get filtered queryset
            queryset = self.repository.get_filtered_queryset(filters)
            
            # Get aggregates before pagination
            aggregates = self.repository.get_aggregates(queryset)
            
            # Paginate results
            paginator = Paginator(queryset, page_size)
            page_obj = paginator.get_page(page)
            
            # Transform to dictionary
            transactions = []
            for txn in page_obj:
                transactions.append(self._serialize_transaction(txn))
            
            return {
                'transactions': transactions,
                'total': paginator.count,
                'pages': paginator.num_pages,
                'page': page,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
                'aggregates': aggregates
            }
        except Exception as e:
            logger.error(f"Error fetching transactions: {str(e)}")
            raise
    
    def get_transaction_by_id(self, txn_id: str) -> Optional[Dict[str, Any]]:
        """Get single transaction details"""
        try:
            transaction = self.repository.get_by_id(txn_id)
            if not transaction:
                return None
            
            # Get related data
            settlement = self._get_settlement_details(txn_id)
            refund = self._get_refund_details(txn_id)
            recon = self._get_reconciliation_details(txn_id)
            
            # Serialize with related data
            result = self._serialize_transaction(transaction)
            result['settlement_details'] = settlement
            result['refund_details'] = refund
            result['reconciliation'] = recon
            
            return result
        except Exception as e:
            logger.error(f"Error fetching transaction {txn_id}: {str(e)}")
            raise
    
    def get_transaction_stats(self, date_range: str = '24h') -> Dict[str, Any]:
        """Get transaction statistics for dashboard"""
        try:
            # Calculate date filter
            end_date = timezone.now()
            if date_range == '24h':
                start_date = end_date - timedelta(hours=24)
            elif date_range == '7d':
                start_date = end_date - timedelta(days=7)
            elif date_range == '30d':
                start_date = end_date - timedelta(days=30)
            else:
                start_date = end_date - timedelta(hours=24)
            
            # Get transactions in range
            transactions = TransactionDetail.objects.filter(
                trans_date__gte=start_date,
                trans_date__lte=end_date
            )
            
            # Calculate stats
            total = transactions.count()
            successful = transactions.filter(status='SUCCESS').count()
            failed = transactions.filter(status='FAILED').count()
            pending = transactions.filter(status='PENDING').count()
            
            # Calculate amounts
            total_amount = transactions.filter(
                status='SUCCESS'
            ).aggregate(
                total=Sum('paid_amount')
            )['total'] or Decimal('0')
            
            # Success rate
            success_rate = (successful / total * 100) if total > 0 else 0
            
            # Payment mode distribution
            payment_modes = transactions.values('payment_mode').annotate(
                count=Count('txn_id'),
                amount=Sum('paid_amount')
            ).order_by('-count')[:5]
            
            return {
                'total_transactions': total,
                'successful': successful,
                'failed': failed,
                'pending': pending,
                'total_amount': float(total_amount),
                'success_rate': round(success_rate, 2),
                'payment_modes': list(payment_modes),
                'date_range': date_range,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
        except Exception as e:
            logger.error(f"Error calculating transaction stats: {str(e)}")
            raise
    
    def _serialize_transaction(self, txn: TransactionDetail) -> Dict[str, Any]:
        """Serialize transaction to dictionary"""
        return {
            'txn_id': txn.txn_id,
            'amount': float(txn.paid_amount or 0),
            'status': txn.status,
            'payment_mode': txn.payment_mode,
            'client_code': txn.client_code,
            'client_name': txn.client_name,
            'payee_name': txn.customer_name,
            'payee_email': txn.payee_email,
            'payee_mob': txn.payee_mob,
            'trans_date': txn.trans_date.isoformat() if txn.trans_date else None,
            'pg_name': txn.pg_name,
            'bank_name': txn.bank_name,
            'is_settled': txn.is_settled,
            'settlement_status': txn.settlement_status,
            'settlement_amount': float(txn.settlement_amount or 0),
            'total_fees': float(txn.total_fees),
            'net_amount': float(txn.net_settlement_amount),
            'is_refundable': txn.is_refundable,
            'has_chargeback': txn.has_chargeback,
            'refund_amount': float(txn.refunded_amount or 0),
            'formatted_amount': txn.formatted_amount
        }
    
    def _get_settlement_details(self, txn_id: str) -> Optional[Dict[str, Any]]:
        """Get settlement details for transaction"""
        try:
            settlement = SettledTransactions.objects.filter(
                transaction_id=txn_id
            ).first()
            
            if settlement:
                return {
                    'settlement_date': settlement.payment_date.isoformat() if settlement.payment_date else None,
                    'net_amount': float(settlement.net_amount or 0),
                    'gross_amount': float(settlement.gross_amount or 0),
                    'fees': float(settlement.conv_fee or 0),
                    'gst': float(settlement.gst_fee or 0),
                    'payout_status': settlement.payout_status,
                    'bank_name': settlement.bank_name
                }
            return None
        except Exception:
            return None
    
    def _get_refund_details(self, txn_id: str) -> Optional[Dict[str, Any]]:
        """Get refund details for transaction"""
        try:
            refunds = RefundRequestFromClient.objects.filter(
                txn_id=txn_id
            ).order_by('-request_date')
            
            refund_list = []
            for refund in refunds:
                refund_list.append({
                    'refund_id': refund.refund_id,
                    'amount': float(refund.refund_amount or 0),
                    'reason': refund.refund_reason,
                    'status': refund.approval_status,
                    'request_date': refund.request_date.isoformat() if refund.request_date else None,
                    'approved_by': refund.approved_by,
                    'bank_ref': refund.bank_ref
                })
            
            return refund_list if refund_list else None
        except Exception:
            return None
    
    def _get_reconciliation_details(self, txn_id: str) -> Optional[Dict[str, Any]]:
        """Get reconciliation details for transaction"""
        try:
            recon = TransactionReconTable.objects.filter(
                txn_id=txn_id
            ).first()
            
            if recon:
                return {
                    'bank_ref': recon.bank_ref,
                    'bank_amount': float(recon.bank_amount or 0),
                    'our_amount': float(recon.our_amount or 0),
                    'difference': float(recon.difference or 0),
                    'status': recon.status,
                    'recon_date': recon.recon_date.isoformat() if recon.recon_date else None,
                    'remarks': recon.remarks
                }
            return None
        except Exception:
            return None


class RefundService(IRefundService):
    """
    Service for handling refunds
    Interface Segregation: Specific interface for refund operations
    """
    
    def __init__(self):
        self.transaction_repo = TransactionRepository()
    
    def initiate_refund(
        self, 
        txn_id: str, 
        amount: Decimal, 
        reason: str, 
        user: Any
    ) -> RefundRequestFromClient:
        """Initiate a refund request"""
        try:
            # Validate transaction
            transaction = self.transaction_repo.get_by_id(txn_id)
            if not transaction:
                raise ValueError(f"Transaction {txn_id} not found")
            
            if not transaction.is_refundable:
                raise ValueError(f"Transaction {txn_id} is not refundable")
            
            if amount > (transaction.paid_amount or 0):
                raise ValueError("Refund amount exceeds transaction amount")
            
            # Create refund request
            with db_transaction.atomic():
                refund = RefundRequestFromClient.objects.create(
                    txn_id=txn_id,
                    client_id=transaction.client_id,
                    refund_amount=amount,
                    refund_reason=reason,
                    request_date=timezone.now(),
                    approval_status='PENDING'
                )
                
                # Update transaction
                transaction.refund_status_code = 'INITIATED'
                transaction.refund_initiated_on = timezone.now()
                transaction.refund_request_from = user.username if user else 'System'
                transaction.save()
                
                return refund
        except Exception as e:
            logger.error(f"Error initiating refund: {str(e)}")
            raise
    
    def approve_refund(self, refund_id: int, approver: Any) -> RefundRequestFromClient:
        """Approve a refund request"""
        try:
            with db_transaction.atomic():
                refund = RefundRequestFromClient.objects.select_for_update().get(
                    refund_id=refund_id
                )
                
                if refund.approval_status != 'PENDING':
                    raise ValueError("Refund is not in pending status")
                
                # Update refund
                refund.approval_status = 'APPROVED'
                refund.approved_by = approver.username if approver else 'System'
                refund.approved_date = timezone.now()
                refund.save()
                
                # Update transaction
                transaction = TransactionDetail.objects.get(txn_id=refund.txn_id)
                transaction.refund_status_code = 'APPROVED'
                transaction.save()
                
                # Trigger refund processing (async task)
                self._process_refund_async(refund)
                
                return refund
        except Exception as e:
            logger.error(f"Error approving refund: {str(e)}")
            raise
    
    def reject_refund(self, refund_id: int, reason: str) -> RefundRequestFromClient:
        """Reject a refund request"""
        try:
            with db_transaction.atomic():
                refund = RefundRequestFromClient.objects.select_for_update().get(
                    refund_id=refund_id
                )
                
                if refund.approval_status != 'PENDING':
                    raise ValueError("Refund is not in pending status")
                
                refund.approval_status = 'REJECTED'
                refund.save()
                
                # Update transaction
                transaction = TransactionDetail.objects.get(txn_id=refund.txn_id)
                transaction.refund_status_code = 'REJECTED'
                transaction.refund_message = reason
                transaction.save()
                
                return refund
        except Exception as e:
            logger.error(f"Error rejecting refund: {str(e)}")
            raise
    
    def get_refunds(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get list of refunds with filters"""
        try:
            queryset = RefundRequestFromClient.objects.all()
            
            if filters.get('status'):
                queryset = queryset.filter(approval_status=filters['status'])
            
            if filters.get('txn_id'):
                queryset = queryset.filter(txn_id=filters['txn_id'])
            
            if filters.get('client_id'):
                queryset = queryset.filter(client_id=filters['client_id'])
            
            refunds = []
            for refund in queryset[:100]:  # Limit to 100
                refunds.append({
                    'refund_id': refund.refund_id,
                    'txn_id': refund.txn_id,
                    'amount': float(refund.refund_amount or 0),
                    'reason': refund.refund_reason,
                    'status': refund.approval_status,
                    'request_date': refund.request_date.isoformat() if refund.request_date else None,
                    'approved_by': refund.approved_by,
                    'approved_date': refund.approved_date.isoformat() if refund.approved_date else None
                })
            
            return refunds
        except Exception as e:
            logger.error(f"Error fetching refunds: {str(e)}")
            raise
    
    def _process_refund_async(self, refund: RefundRequestFromClient):
        """Process refund asynchronously (placeholder for actual implementation)"""
        # This would trigger an async task to process the refund with payment gateway
        pass


class SettlementService(ISettlementService):
    """
    Service for settlement operations
    Dependency Inversion: Depends on abstractions, not concrete implementations
    """
    
    def __init__(self):
        self.transaction_repo = TransactionRepository()
    
    def get_pending_settlements(self, client_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get pending settlements"""
        try:
            filters = {'is_settled': False, 'status': 'SUCCESS'}
            if client_id:
                filters['client_id'] = client_id
            
            queryset = self.transaction_repo.get_filtered_queryset(filters)
            aggregates = self.transaction_repo.get_aggregates(queryset)
            
            return {
                'total_count': aggregates['total_transactions'] or 0,
                'total_amount': float(aggregates['total_amount'] or 0),
                'total_fees': float(aggregates['total_fees'] or 0),
                'net_amount': float((aggregates['total_amount'] or 0) - (aggregates['total_fees'] or 0))
            }
        except Exception as e:
            logger.error(f"Error fetching pending settlements: {str(e)}")
            raise
    
    def process_settlement_batch(self, txn_ids: List[str]) -> Dict[str, Any]:
        """Process batch settlement"""
        try:
            with db_transaction.atomic():
                # Update settlement status
                updated = self.transaction_repo.bulk_update_settlement_status(
                    txn_ids, 
                    'PROCESSING'
                )
                
                # Create settlement record
                settlement = SettledTransactions.objects.create(
                    transaction_id=','.join(txn_ids),
                    transaction_status='BATCH_PROCESSING',
                    created_on=timezone.now(),
                    payout_status=False
                )
                
                return {
                    'settlement_id': settlement.id,
                    'transactions_updated': updated,
                    'status': 'PROCESSING'
                }
        except Exception as e:
            logger.error(f"Error processing settlement batch: {str(e)}")
            raise


class TransactionAnalyticsService(IAnalyticsService):
    """
    Service for transaction analytics
    Single Responsibility: Analytics and reporting
    """
    
    def __init__(self):
        self.cache_timeout = 300  # 5 minutes
    
    def get_payment_mode_distribution(self, date_range: str = '7d') -> List[Dict[str, Any]]:
        """Get payment mode distribution"""
        cache_key = f'payment_mode_dist_{date_range}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            end_date = timezone.now()
            if date_range == '7d':
                start_date = end_date - timedelta(days=7)
            elif date_range == '30d':
                start_date = end_date - timedelta(days=30)
            else:
                start_date = end_date - timedelta(days=7)
            
            distribution = TransactionDetail.objects.filter(
                trans_date__gte=start_date,
                trans_date__lte=end_date,
                status='SUCCESS'
            ).values('payment_mode').annotate(
                count=Count('txn_id'),
                total_amount=Sum('paid_amount')
            ).order_by('-total_amount')
            
            result = []
            for item in distribution:
                result.append({
                    'payment_mode': item['payment_mode'] or 'Unknown',
                    'count': item['count'],
                    'amount': float(item['total_amount'] or 0)
                })
            
            cache.set(cache_key, result, self.cache_timeout)
            return result
        except Exception as e:
            logger.error(f"Error calculating payment mode distribution: {str(e)}")
            return []
    
    def get_hourly_transaction_volume(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get hourly transaction volume"""
        cache_key = f'hourly_volume_{hours}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            end_time = timezone.now()
            start_time = end_time - timedelta(hours=hours)
            
            # This would require raw SQL for hour grouping
            # Simplified version
            result = []
            for i in range(hours):
                hour_start = start_time + timedelta(hours=i)
                hour_end = hour_start + timedelta(hours=1)
                
                volume = TransactionDetail.objects.filter(
                    trans_date__gte=hour_start,
                    trans_date__lt=hour_end
                ).aggregate(
                    count=Count('txn_id'),
                    amount=Sum('paid_amount')
                )
                
                result.append({
                    'hour': hour_start.strftime('%Y-%m-%d %H:00'),
                    'count': volume['count'] or 0,
                    'amount': float(volume['amount'] or 0)
                })
            
            cache.set(cache_key, result, self.cache_timeout)
            return result
        except Exception as e:
            logger.error(f"Error calculating hourly volume: {str(e)}")
            return []
    
    def get_top_clients_by_volume(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top clients by transaction volume"""
        cache_key = f'top_clients_{limit}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            # Last 30 days
            start_date = timezone.now() - timedelta(days=30)
            
            top_clients = TransactionDetail.objects.filter(
                trans_date__gte=start_date,
                status='SUCCESS'
            ).values('client_code', 'client_name').annotate(
                transaction_count=Count('txn_id'),
                total_amount=Sum('paid_amount'),
                avg_amount=Avg('paid_amount')
            ).order_by('-total_amount')[:limit]
            
            result = []
            for client in top_clients:
                result.append({
                    'client_code': client['client_code'],
                    'client_name': client['client_name'] or 'Unknown',
                    'transaction_count': client['transaction_count'],
                    'total_amount': float(client['total_amount'] or 0),
                    'avg_amount': float(client['avg_amount'] or 0)
                })
            
            cache.set(cache_key, result, self.cache_timeout)
            return result
        except Exception as e:
            logger.error(f"Error fetching top clients: {str(e)}")
            return []


class DisputeService:
    """
    Service for handling transaction disputes and chargebacks
    """
    
    def get_open_disputes(self) -> List[Dict[str, Any]]:
        """Get open disputes"""
        try:
            disputes = TransactionDetail.objects.filter(
                is_charge_back=True,
                charge_back_status__in=['OPEN', 'PENDING', 'INVESTIGATING']
            ).values(
                'txn_id', 
                'charge_back_amount',
                'charge_back_date',
                'charge_back_status',
                'charge_back_remarks'
            )[:100]
            
            result = []
            for dispute in disputes:
                result.append({
                    'txn_id': dispute['txn_id'],
                    'amount': float(dispute['charge_back_amount'] or 0),
                    'date': dispute['charge_back_date'].isoformat() if dispute['charge_back_date'] else None,
                    'status': dispute['charge_back_status'],
                    'remarks': dispute['charge_back_remarks']
                })
            
            return result
        except Exception as e:
            logger.error(f"Error fetching disputes: {str(e)}")
            return []
    
    def create_dispute(
        self,
        txn_id: str,
        dispute_type: str,
        reason: str,
        amount: Decimal,
        raised_by: str
    ) -> Dict[str, Any]:
        """Create a new dispute"""
        try:
            with db_transaction.atomic():
                transaction = TransactionDetail.objects.get(txn_id=txn_id)
                
                # Update transaction with chargeback info
                transaction.is_charge_back = True
                transaction.charge_back_amount = amount
                transaction.charge_back_date = timezone.now()
                transaction.charge_back_status = 'OPEN'
                transaction.charge_back_remarks = f"{dispute_type}: {reason}"
                transaction.chargeback_request_from = raised_by
                transaction.save()
                
                return {
                    'txn_id': txn_id,
                    'status': 'CREATED',
                    'dispute_type': dispute_type,
                    'amount': float(amount)
                }
        except Exception as e:
            logger.error(f"Error creating dispute: {str(e)}")
            raise