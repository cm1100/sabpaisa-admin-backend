"""
Transaction API Views
Following SOLID principles and DRF best practices
"""
from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.db import models
import logging
import csv

from .models import TransactionDetail, RefundRequestFromClient, SettledTransactions, TransactionsToSettle
from .services import (
    TransactionService,
    RefundService,
    DisputeService,
    TransactionAnalyticsService
)
from .serializers import (
    TransactionDetailSerializer,
    TransactionListSerializer,
    TransactionStatsSerializer,
    TransactionFilterSerializer,
    RefundSerializer,
    InitiateRefundSerializer,
    DisputeSerializer,
    CreateDisputeSerializer,
    PaymentModeDistributionSerializer,
    HourlyVolumeSerializer,
    TopClientSerializer,
    TransactionExportSerializer
)

logger = logging.getLogger(__name__)


class TransactionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for transaction operations
    Provides CRUD operations for transactions
    """
    queryset = TransactionDetail.objects.all()
    serializer_class = TransactionDetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'txn_id'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.transaction_service = TransactionService()
    
    def list(self, request):
        """List transactions with filters and pagination"""
        try:
            # Validate filters
            filter_serializer = TransactionFilterSerializer(data=request.query_params)
            filter_serializer.is_valid(raise_exception=True)
            filters = filter_serializer.validated_data
            
            # Get transactions
            page = filters.pop('page', 1)
            page_size = filters.pop('page_size', 20)
            result = self.transaction_service.get_transactions(
                filters=filters,
                page=page,
                page_size=page_size
            )
            
            # Serialize and return
            serializer = TransactionListSerializer(result['transactions'], many=True)
            
            return Response({
                'results': serializer.data,
                'count': result['total'],
                'next': result['has_next'],
                'previous': result['has_previous'],
                'total_pages': result['pages'],
                'current_page': result['page']
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error listing transactions: {str(e)}")
            return Response(
                {"error": "Failed to fetch transactions"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def retrieve(self, request, txn_id=None):
        """Get single transaction details"""
        try:
            transaction = self.transaction_service.get_transaction_by_id(txn_id)
            
            if not transaction:
                return Response(
                    {"error": "Transaction not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(transaction, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error retrieving transaction: {str(e)}")
            return Response(
                {"error": "Failed to fetch transaction"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get transaction statistics"""
        try:
            date_range = request.query_params.get('range', '24h')
            stats = self.transaction_service.get_transaction_stats(date_range)
            
            serializer = TransactionStatsSerializer(stats)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching transaction stats: {str(e)}")
            return Response(
                {"error": "Failed to fetch statistics"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def live(self, request):
        """Get live/recent transactions for monitoring"""
        try:
            from datetime import datetime, timedelta
            
            # Get transactions from last hour by default
            time_range = request.query_params.get('range', '1h')
            
            if time_range == '1h':
                date_from = datetime.now() - timedelta(hours=1)
            elif time_range == '30m':
                date_from = datetime.now() - timedelta(minutes=30)
            elif time_range == '5m':
                date_from = datetime.now() - timedelta(minutes=5)
            else:
                date_from = datetime.now() - timedelta(hours=1)
            
            # Get recent transactions
            transactions = TransactionDetail.objects.filter(
                trans_date__gte=date_from
            ).order_by('-trans_date')[:100]  # Limit to 100 most recent
            
            serializer = TransactionListSerializer(transactions, many=True)
            
            # Calculate stats
            total = transactions.count()
            success = transactions.filter(status='SUCCESS').count()
            failed = transactions.filter(status='FAILED').count()
            pending = transactions.filter(status='PENDING').count()
            
            success_txns = transactions.filter(status='SUCCESS')
            total_volume = success_txns.aggregate(
                total=models.Sum('paid_amount')
            )['total'] or 0
            
            return Response({
                'transactions': serializer.data,
                'stats': {
                    'total': total,
                    'success': success,
                    'failed': failed,
                    'pending': pending,
                    'success_rate': (success / total * 100) if total > 0 else 0,
                    'total_volume': float(total_volume)
                },
                'timestamp': datetime.now().isoformat()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching live transactions: {str(e)}")
            return Response(
                {"error": "Failed to fetch live transactions"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export transactions to CSV/Excel"""
        try:
            # Validate export parameters
            export_serializer = TransactionExportSerializer(data=request.query_params)
            export_serializer.is_valid(raise_exception=True)
            params = export_serializer.validated_data
            
            # Get transactions for export
            filters = {
                'date_from': params.get('date_from'),
                'date_to': params.get('date_to'),
                'status': params.get('status'),
                'client_code': params.get('client_code'),
            }
            
            result = self.transaction_service.get_transactions(
                filters={k: v for k, v in filters.items() if v},
                page=1,
                page_size=10000  # Export limit
            )
            
            # Create CSV response
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
            
            writer = csv.writer(response)
            writer.writerow([
                'Transaction ID', 'Amount', 'Status', 'Payment Mode',
                'Client Code', 'Payee Name', 'Email', 'Contact',
                'Transaction Date', 'Gateway'
            ])
            
            for txn in result['transactions']:
                writer.writerow([
                    txn['txn_id'],
                    txn['amount'],
                    txn['status'],
                    txn['payment_mode'],
                    txn['client_code'],
                    txn['payee_name'],
                    txn['email'],
                    txn['contact_no'],
                    txn['trans_date'],
                    txn['pg_name']
                ])
            
            return response
            
        except Exception as e:
            logger.error(f"Error exporting transactions: {str(e)}")
            return Response(
                {"error": "Failed to export transactions"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RefundView(APIView):
    """
    API View for refund operations
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.refund_service = RefundService()
    
    def get(self, request):
        """Get list of refunds"""
        try:
            filters = {
                'status': request.query_params.get('status'),
                'txn_id': request.query_params.get('txn_id'),
            }
            
            refunds = self.refund_service.get_refunds(
                filters={k: v for k, v in filters.items() if v}
            )
            
            return Response(refunds, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching refunds: {str(e)}")
            return Response(
                {"error": "Failed to fetch refunds"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """Initiate a new refund"""
        try:
            serializer = InitiateRefundSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            refund = self.refund_service.initiate_refund(
                txn_id=serializer.validated_data['txn_id'],
                amount=serializer.validated_data['amount'],
                reason=serializer.validated_data['reason'],
                user=request.user
            )
            
            refund_serializer = RefundSerializer(refund)
            return Response(refund_serializer.data, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error initiating refund: {str(e)}")
            return Response(
                {"error": "Failed to initiate refund"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RefundApprovalView(APIView):
    """
    API View for refund approval
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.refund_service = RefundService()
    
    def post(self, request, refund_id):
        """Approve a refund"""
        try:
            refund = self.refund_service.approve_refund(refund_id, request.user)
            
            serializer = RefundSerializer(refund)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error approving refund: {str(e)}")
            return Response(
                {"error": "Failed to approve refund"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DisputeView(APIView):
    """
    API View for dispute management
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dispute_service = DisputeService()
    
    def get(self, request):
        """Get open disputes"""
        try:
            disputes = self.dispute_service.get_open_disputes()
            return Response(disputes, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching disputes: {str(e)}")
            return Response(
                {"error": "Failed to fetch disputes"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """Create a new dispute"""
        try:
            serializer = CreateDisputeSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            dispute = self.dispute_service.create_dispute(
                txn_id=serializer.validated_data['txn_id'],
                dispute_type=serializer.validated_data['dispute_type'],
                reason=serializer.validated_data['reason'],
                amount=serializer.validated_data['amount'],
                raised_by=request.user.username
            )
            
            dispute_serializer = DisputeSerializer(dispute)
            return Response(dispute_serializer.data, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error creating dispute: {str(e)}")
            return Response(
                {"error": "Failed to create dispute"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TransactionAnalyticsView(APIView):
    """
    API View for transaction analytics
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.analytics_service = TransactionAnalyticsService()
    
    @method_decorator(cache_page(300))  # Cache for 5 minutes
    def get(self, request):
        """Get transaction analytics"""
        try:
            analytics_type = request.query_params.get('type', 'payment_modes')
            
            if analytics_type == 'payment_modes':
                date_range = request.query_params.get('range', '7d')
                data = self.analytics_service.get_payment_mode_distribution(date_range)
                serializer = PaymentModeDistributionSerializer(data, many=True)
                
            elif analytics_type == 'hourly_volume':
                hours = int(request.query_params.get('hours', 24))
                data = self.analytics_service.get_hourly_transaction_volume(hours)
                serializer = HourlyVolumeSerializer(data, many=True)
                
            elif analytics_type == 'top_clients':
                limit = int(request.query_params.get('limit', 10))
                data = self.analytics_service.get_top_clients_by_volume(limit)
                serializer = TopClientSerializer(data, many=True)
                
            else:
                return Response(
                    {"error": "Invalid analytics type"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching analytics: {str(e)}")
            return Response(
                {"error": "Failed to fetch analytics"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# Settlement Views
class SettlementSummaryView(APIView):
    """
    API View for settlement summary dashboard
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get settlement summary statistics"""
        try:
            from datetime import datetime, timedelta
            from django.utils import timezone
            from django.db.models import Count, Sum, Q
            
            today = timezone.now().date()
            week_ago = today - timedelta(days=7)
            month_ago = today - timedelta(days=30)
            
            # Pending settlements from transaction_detail
            pending = TransactionDetail.objects.filter(
                status='SUCCESS',
                is_settled=False
            ).aggregate(
                count=Count('txn_id'),
                amount=Sum('settlement_amount')
            )
            
            # Settled transactions from settled_transactions table
            settled_today = SettledTransactions.objects.filter(
                trans_date=today
            ).aggregate(
                count=Count('id'),
                amount=Sum('settlement_amount')
            )
            
            settled_week = SettledTransactions.objects.filter(
                trans_date__gte=week_ago
            ).aggregate(
                count=Count('id'),
                amount=Sum('settlement_amount')
            )
            
            settled_month = SettledTransactions.objects.filter(
                trans_date__gte=month_ago
            ).aggregate(
                count=Count('id'),
                amount=Sum('settlement_amount')
            )
            
            # In process from transactions_to_settle
            in_process = TransactionsToSettle.objects.filter(
                payout_status__in=['PROCESSING', 'PENDING']
            ).aggregate(
                count=Count('id'),
                amount=Sum('settlement_amount')
            )
            
            summary_data = {
                'pending_count': pending['count'] or 0,
                'pending_amount': float(pending['amount'] or 0),
                'settled_today_count': settled_today['count'] or 0,
                'settled_today_amount': float(settled_today['amount'] or 0),
                'settled_week_count': settled_week['count'] or 0,
                'settled_week_amount': float(settled_week['amount'] or 0),
                'settled_month_count': settled_month['count'] or 0,
                'settled_month_amount': float(settled_month['amount'] or 0),
                'in_process_count': in_process['count'] or 0,
                'in_process_amount': float(in_process['amount'] or 0)
            }
            
            from .serializers import SettlementSummarySerializer
            serializer = SettlementSummarySerializer(summary_data)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching settlement summary: {str(e)}")
            return Response(
                {"error": "Failed to fetch settlement summary"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PendingSettlementsView(APIView):
    """
    API View for pending settlements list
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get list of pending settlements"""
        try:
            from datetime import datetime
            from django.utils import timezone
            
            client_code = request.query_params.get('client_code')
            sort_by = request.query_params.get('sort_by', '-trans_date')
            
            queryset = TransactionDetail.objects.filter(
                status='SUCCESS',
                is_settled=False
            )
            
            if client_code:
                queryset = queryset.filter(client_code=client_code)
            
            queryset = queryset.order_by(sort_by)[:100]  # Limit to 100 records
            
            pending_list = []
            for txn in queryset:
                # Calculate age in days
                age_in_days = 0
                if txn.trans_date:
                    # Handle timezone awareness
                    now = timezone.now()
                    trans_date = txn.trans_date
                    if trans_date.tzinfo is None:
                        trans_date = timezone.make_aware(trans_date)
                    age_in_days = (now - trans_date).days
                
                pending_data = {
                    'txn_id': txn.txn_id,
                    'client_id': txn.client_id or '',
                    'client_name': txn.client_name or '',
                    'client_code': txn.client_code or '',
                    'paid_amount': float(txn.paid_amount or 0),
                    'settlement_amount': float(txn.settlement_amount or txn.paid_amount or 0),
                    'payee_name': txn.customer_name,
                    'payee_email': txn.payee_email or '',
                    'payee_mob': txn.payee_mob or '',
                    'trans_date': txn.trans_date,
                    'payment_mode': txn.payment_mode or '',
                    'status': txn.status,
                    'age_in_days': age_in_days,
                    'formatted_amount': txn.formatted_amount
                }
                pending_list.append(pending_data)
            
            from .serializers import PendingSettlementSerializer
            serializer = PendingSettlementSerializer(pending_list, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching pending settlements: {str(e)}")
            return Response(
                {"error": "Failed to fetch pending settlements"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SettledTransactionsView(APIView):
    """
    API View for settled transactions
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get list of settled transactions"""
        try:
            from datetime import datetime, timedelta
            
            client_code = request.query_params.get('client_code')
            date_from = request.query_params.get('date_from')
            date_to = request.query_params.get('date_to')
            
            queryset = SettledTransactions.objects.all()
            
            # Apply filters
            if date_from:
                from django.utils.dateparse import parse_date
                date_obj = parse_date(date_from) if isinstance(date_from, str) else date_from
                if date_obj:
                    queryset = queryset.filter(trans_date__gte=date_obj)
            
            if date_to:
                from django.utils.dateparse import parse_date
                date_obj = parse_date(date_to) if isinstance(date_to, str) else date_to
                if date_obj:
                    queryset = queryset.filter(trans_date__lte=date_obj)
            
            queryset = queryset.order_by('-trans_date')[:100]
            
            from .serializers import SettledTransactionSerializer
            serializer = SettledTransactionSerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching settled transactions: {str(e)}")
            return Response(
                {"error": "Failed to fetch settled transactions"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProcessBatchSettlementView(APIView):
    """
    API View for processing batch settlements
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Process a batch of settlements"""
        try:
            from .serializers import BatchSettlementRequestSerializer
            from django.utils import timezone
            from django.db import transaction
            import uuid
            
            serializer = BatchSettlementRequestSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            transaction_ids = serializer.validated_data['transaction_ids']
            settlement_date = serializer.validated_data.get('settlement_date', timezone.now())
            remarks = serializer.validated_data.get('remarks', '')
            
            # Generate batch ID
            batch_id = f"BATCH_{timezone.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6].upper()}"
            
            processed = []
            failed = []
            
            with transaction.atomic():
                for txn_id in transaction_ids:
                    try:
                        # Get transaction
                        txn = TransactionDetail.objects.get(
                            txn_id=txn_id,
                            status='SUCCESS',
                            is_settled=False
                        )
                        
                        logger.info(f"Processing transaction {txn_id}")
                        
                        # Create settlement record in settled_transactions table
                        # Calculate amounts safely
                        settlement_amt = txn.settlement_amount if txn.settlement_amount else (txn.paid_amount if txn.paid_amount else 0)
                        paid_amt = txn.paid_amount if txn.paid_amount else 0
                        
                        SettledTransactions.objects.create(
                            transaction_id=txn.txn_id,
                            bank_name=(txn.bank_name if txn.bank_name and txn.bank_name != 'NA' else 'Unknown Bank'),
                            transaction_mode=(txn.payment_mode if txn.payment_mode and txn.payment_mode != 'NA' else 'Unknown'),
                            trans_date=settlement_date.date(),
                            net_amount=float(settlement_amt),
                            gross_amount=float(paid_amt),
                            currency='INR',
                            conv_fee=str(txn.convcharges or '0.00'),
                            gst_fee=str(txn.gst or '0.00'),
                            pipe_fee=str(txn.ep_charges or '0.00'),
                            transaction_status='SETTLED',
                            payout_status=True,
                            name=(txn.payee_first_name if txn.payee_first_name and txn.payee_first_name != 'NA' else 'Unknown Customer'),
                            email=(txn.payee_email if txn.payee_email and txn.payee_email != 'NA' else None),
                            mobile_number=(txn.payee_mob if txn.payee_mob and txn.payee_mob != 'NA' else None),
                            settlement_amount=float(settlement_amt),
                            payment_date=settlement_date.date(),
                            created_by=request.user.username if hasattr(request.user, 'username') else 'system',
                            company_domain=(txn.client_code if txn.client_code and txn.client_code != 'NA' else 'Unknown')
                        )
                        
                        # Update transaction as settled
                        txn.is_settled = True
                        txn.settlement_date = settlement_date
                        txn.settlement_status = 'COMPLETED'
                        txn.settlement_utr = f"UTR{timezone.now().strftime('%Y%m%d%H%M%S')}{txn_id[-4:]}"
                        txn.settlement_by = request.user.username if hasattr(request.user, 'username') else 'system'
                        if remarks:
                            txn.settlement_remarks = remarks
                        txn.save()
                        
                        # Remove from settlement queue if exists
                        TransactionsToSettle.objects.filter(transaction_id=txn_id).delete()
                        
                        processed.append(txn_id)
                        
                    except TransactionDetail.DoesNotExist:
                        failed.append({
                            'txn_id': txn_id,
                            'error': 'Transaction not found or not eligible for settlement'
                        })
                    except Exception as e:
                        failed.append({
                            'txn_id': txn_id,
                            'error': str(e)
                        })
            
            from .serializers import SettlementBatchSerializer
            batch_data = {
                'batch_id': batch_id,
                'settlement_date': settlement_date,
                'total_transactions': len(processed),
                'total_amount': sum([
                    float(TransactionDetail.objects.get(txn_id=tid).settlement_amount or 
                          TransactionDetail.objects.get(txn_id=tid).paid_amount or 0)
                    for tid in processed
                ]) if processed else 0,
                'status': 'COMPLETED' if processed else 'FAILED',
                'created_at': timezone.now(),
                'processed_transactions': processed,
                'failed_transactions': failed
            }
            
            logger.info(f"Batch settlement {batch_id}: {len(processed)} processed, {len(failed)} failed")
            
            return Response({
                'batch_id': batch_id,
                'processed': len(processed),
                'failed': len(failed),
                'failed_transactions': failed,
                'message': f'Batch settlement processed: {len(processed)} successful, {len(failed)} failed'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error processing batch settlement: {str(e)}")
            return Response(
                {"error": f"Failed to process batch settlement: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ClientSettlementSummaryView(APIView):
    """
    API View for client-wise settlement summary
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get settlement summary by client"""
        try:
            from django.db.models import Q, Sum, Count
            
            # Get clients with pending or settled transactions
            clients_data = TransactionDetail.objects.values(
                'client_id', 'client_name', 'client_code'
            ).annotate(
                pending_count=Count('txn_id', filter=Q(is_settled=False, status='SUCCESS')),
                pending_amount=Sum('settlement_amount', filter=Q(is_settled=False, status='SUCCESS')),
                settled_count=Count('txn_id', filter=Q(is_settled=True)),
                settled_amount=Sum('settlement_amount', filter=Q(is_settled=True))
            ).filter(
                Q(pending_count__gt=0) | Q(settled_count__gt=0)
            ).order_by('client_name')
            
            client_summaries = []
            for client in clients_data:
                # Get last settlement date from settled_transactions
                last_settled = SettledTransactions.objects.filter(
                    company_domain=client['client_code']
                ).order_by('-trans_date').first()
                
                # Convert date to datetime for serialization
                last_settlement_date = None
                if last_settled and last_settled.trans_date:
                    from datetime import datetime
                    from django.utils import timezone
                    if isinstance(last_settled.trans_date, datetime):
                        last_settlement_date = last_settled.trans_date
                    else:  # date object
                        last_settlement_date = datetime.combine(last_settled.trans_date, datetime.min.time())
                        last_settlement_date = timezone.make_aware(last_settlement_date)
                
                client_summary = {
                    'client_id': client['client_id'] or '',
                    'client_name': client['client_name'] or 'Unknown Client',
                    'client_code': client['client_code'] or '',
                    'pending_count': client['pending_count'] or 0,
                    'pending_amount': float(client['pending_amount'] or 0),
                    'settled_count': client['settled_count'] or 0,
                    'settled_amount': float(client['settled_amount'] or 0),
                    'last_settlement_date': last_settlement_date,
                    'formatted_pending_amount': f"₹{float(client['pending_amount'] or 0):,.2f}",
                    'formatted_settled_amount': f"₹{float(client['settled_amount'] or 0):,.2f}"
                }
                client_summaries.append(client_summary)
            
            from .serializers import ClientSettlementSummarySerializer
            serializer = ClientSettlementSummarySerializer(client_summaries, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching client settlement summary: {str(e)}")
            return Response(
                {"error": "Failed to fetch client settlement summary"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ExportPendingSettlementsView(APIView):
    """
    API View for exporting pending settlements to CSV
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Export pending settlements to CSV"""
        try:
            from django.utils import timezone
            
            # Get pending settlements
            queryset = TransactionDetail.objects.filter(
                status='SUCCESS',
                is_settled=False
            ).order_by('-trans_date')[:1000]  # Limit for performance
            
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="pending_settlements_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
            
            writer = csv.writer(response)
            writer.writerow([
                'Transaction ID', 'Client Code', 'Client Name', 'Customer Name',
                'Amount', 'Settlement Amount', 'Payment Mode', 'Transaction Date',
                'Email', 'Mobile', 'Status', 'Age (Days)'
            ])
            
            for txn in queryset:
                age_days = 0
                if txn.trans_date:
                    # Handle timezone awareness
                    now = timezone.now()
                    trans_date = txn.trans_date
                    if trans_date.tzinfo is None:
                        trans_date = timezone.make_aware(trans_date)
                    age_days = (now - trans_date).days
                
                writer.writerow([
                    txn.txn_id,
                    txn.client_code or '',
                    txn.client_name or '',
                    txn.customer_name,
                    float(txn.paid_amount or 0),
                    float(txn.settlement_amount or txn.paid_amount or 0),
                    txn.payment_mode or '',
                    txn.trans_date.strftime('%Y-%m-%d %H:%M:%S') if txn.trans_date else '',
                    txn.payee_email or '',
                    txn.payee_mob or '',
                    txn.status,
                    age_days
                ])
            
            logger.info(f"Exported {queryset.count()} pending settlements to CSV")
            return response
            
        except Exception as e:
            logger.error(f"Error exporting pending settlements: {str(e)}")
            return Response(
                {"error": "Failed to export pending settlements"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )