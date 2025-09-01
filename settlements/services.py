"""
Settlement Services
Following SOLID principles with proper separation of concerns
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, date
from datetime import datetime as dt
from decimal import Decimal
from django.db.models import Q, Sum, Count, Avg, F
from django.db import transaction
from django.utils import timezone
from django.core.cache import cache
import logging
import csv
import io

from .models import (
    SettlementBatch,
    SettlementDetail,
    SettlementReport,
    SettlementConfiguration,
    SettlementReconciliation
)
from transactions.models import TransactionDetail
logger = logging.getLogger(__name__)


class SettlementProcessingService:
    """
    Service for processing settlements
    Single Responsibility: Settlement batch processing
    """
    
    def __init__(self):
        self.batch_model = SettlementBatch
        self.detail_model = SettlementDetail
        self.config_model = SettlementConfiguration
        self.transaction_model = TransactionDetail
    
    @transaction.atomic
    def create_settlement_batch(self, batch_date: date = None, user=None) -> SettlementBatch:
        """
        Create a new settlement batch for processing
        """
        try:
            if not batch_date:
                batch_date = timezone.now().date()
            
            # Check if batch already exists for the date
            existing_batch = self.batch_model.objects.filter(
                batch_date=batch_date,
                status__in=['PENDING', 'PROCESSING', 'APPROVED']
            ).first()
            
            if existing_batch:
                raise ValueError(f"Active batch already exists for {batch_date}")
            
            # Get eligible transactions for settlement
            eligible_transactions = self.get_eligible_transactions(batch_date)
            
            if not eligible_transactions:
                raise ValueError("No eligible transactions found for settlement")
            
            # Calculate totals
            total_amount = sum(t.act_amount for t in eligible_transactions if t.act_amount)
            total_transactions = len(eligible_transactions)
            
            # Create batch
            batch = self.batch_model.objects.create(
                batch_date=batch_date,
                total_transactions=total_transactions,
                total_amount=total_amount,
                status='PENDING',
                processed_by=user
            )
            
            # Create settlement details for each transaction
            for txn in eligible_transactions:
                self.create_settlement_detail(batch, txn)
            
            # Calculate fees and net amount
            self.calculate_batch_fees(batch)
            
            logger.info(f"Settlement batch {batch.batch_id} created with {total_transactions} transactions")
            
            return batch
            
        except Exception as e:
            logger.error(f"Error creating settlement batch: {str(e)}")
            raise
    
    def get_eligible_transactions(self, batch_date: date) -> List[TransactionDetail]:
        """
        Get transactions eligible for settlement based on T+1 cycle
        """
        try:
            # For T+1, get transactions from previous day
            # Use datetime range to handle timezone properly
            start_date = timezone.make_aware(datetime.combine(
                batch_date - timedelta(days=1), 
                datetime.min.time()
            ))
            end_date = timezone.make_aware(datetime.combine(
                batch_date, 
                datetime.min.time()
            ))
            
            # Get successful transactions not already settled
            eligible = self.transaction_model.objects.filter(
                trans_date__gte=start_date,
                trans_date__lt=end_date,
                status__iexact='SUCCESS',
                is_settled=False  # Direct check for better performance
            )
            
            return list(eligible)
            
        except Exception as e:
            logger.error(f"Error fetching eligible transactions: {str(e)}")
            raise
    
    def create_settlement_detail(self, batch: SettlementBatch, transaction: TransactionDetail) -> SettlementDetail:
        """
        Create individual settlement detail for a transaction
        """
        try:
            # Get client configuration
            config = self.get_client_configuration(transaction.client_code)
            
            # Calculate fees
            transaction_amount = Decimal(str(transaction.act_amount or 0))
            fees = config.calculate_fees(transaction_amount)
            
            # Create settlement detail
            detail = self.detail_model.objects.create(
                batch=batch,
                txn_id=transaction.txn_id,
                client_code=transaction.client_code,
                transaction_amount=transaction_amount,
                settlement_amount=transaction_amount,
                processing_fee=fees['processing_fee'],
                gst_amount=fees['gst'],
                net_amount=fees['net_amount'],
                settlement_status='PENDING'
            )
            
            return detail
            
        except Exception as e:
            logger.error(f"Error creating settlement detail for {transaction.txn_id}: {str(e)}")
            raise
    
    def get_client_configuration(self, client_code: str) -> SettlementConfiguration:
        """
        Get or create settlement configuration for a client
        """
        try:
            config, created = self.config_model.objects.get_or_create(
                client_code=client_code,
                defaults={
                    'settlement_cycle': 'T+1',
                    'processing_fee_percentage': Decimal('2.0'),
                    'gst_percentage': Decimal('18.0'),
                    'min_settlement_amount': Decimal('100'),
                    'auto_settle': True
                }
            )
            
            if created:
                logger.info(f"Created default settlement configuration for client {client_code}")
            
            return config
            
        except Exception as e:
            logger.error(f"Error getting client configuration: {str(e)}")
            raise
    
    def calculate_batch_fees(self, batch: SettlementBatch) -> None:
        """
        Calculate total fees for a batch
        """
        try:
            # Aggregate fees from all details
            totals = batch.settlements.aggregate(
                total_processing_fee=Sum('processing_fee'),
                total_gst=Sum('gst_amount'),
                total_net=Sum('net_amount')
            )
            
            batch.processing_fee = totals['total_processing_fee'] or 0
            batch.gst_amount = totals['total_gst'] or 0
            batch.net_settlement_amount = totals['total_net'] or 0
            batch.save()
            
        except Exception as e:
            logger.error(f"Error calculating batch fees: {str(e)}")
            raise
    
    @transaction.atomic
    def process_settlement_batch(self, batch_id: str, user=None) -> SettlementBatch:
        """
        Process a settlement batch
        """
        try:
            batch = self.batch_model.objects.get(batch_id=batch_id)
            
            if batch.status not in ['PENDING', 'APPROVED']:
                raise ValueError(f"Batch cannot be processed in {batch.status} status")
            
            # Update batch status
            batch.status = 'PROCESSING'
            batch.processed_at = timezone.now()
            batch.processed_by = user
            batch.save()
            
            # Update all settlement details
            batch.settlements.update(
                settlement_status='PROCESSING',
                settlement_date=timezone.now()
            )
            
            # TODO: Integrate with actual payment gateway for processing
            
            # Simulate processing completion
            batch.status = 'COMPLETED'
            batch.save()
            
            # Update settlement details to SETTLED
            settlement_time = timezone.now()
            batch.settlements.update(
                settlement_status='SETTLED',
                settlement_date=settlement_time
            )
            
            # IMPORTANT: Update original transactions as settled
            settled_txn_ids = batch.settlements.values_list('txn_id', flat=True)
            updated_count = self.transaction_model.objects.filter(
                txn_id__in=settled_txn_ids
            ).update(
                is_settled=True,
                settlement_date=settlement_time,
                settlement_status='SETTLED'
            )
            
            logger.info(f"Settlement batch {batch_id} processed successfully")
            logger.info(f"Updated {updated_count} transactions as settled")
            
            return batch
            
        except self.batch_model.DoesNotExist:
            raise ValueError(f"Settlement batch {batch_id} not found")
        except Exception as e:
            logger.error(f"Error processing settlement batch: {str(e)}")
            raise
    
    def get_settlement_batches(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Get list of settlement batches with filters
        """
        try:
            queryset = self.batch_model.objects.all()
            
            if filters:
                if 'status' in filters:
                    queryset = queryset.filter(status=filters['status'])
                if 'batch_date_from' in filters:
                    queryset = queryset.filter(batch_date__gte=filters['batch_date_from'])
                if 'batch_date_to' in filters:
                    queryset = queryset.filter(batch_date__lte=filters['batch_date_to'])
                if 'date_from' in filters:
                    queryset = queryset.filter(batch_date__gte=filters['date_from'])
                if 'date_to' in filters:
                    queryset = queryset.filter(batch_date__lte=filters['date_to'])
                if 'client_code' in filters:
                    # Need to join with settlement details for client filtering
                    queryset = queryset.filter(settlements__client_code__icontains=filters['client_code']).distinct()
                if 'amount_min' in filters:
                    queryset = queryset.filter(total_amount__gte=filters['amount_min'])
                if 'amount_max' in filters:
                    queryset = queryset.filter(total_amount__lte=filters['amount_max'])
            
            batches = []
            for batch in queryset[:50]:  # Limit for performance
                batches.append({
                    'batch_id': str(batch.batch_id),
                    'batch_date': batch.batch_date.isoformat(),
                    'total_transactions': batch.total_transactions,
                    'total_amount': float(batch.total_amount),
                    'processing_fee': float(batch.processing_fee),
                    'gst_amount': float(batch.gst_amount),
                    'net_settlement_amount': float(batch.net_settlement_amount),
                    'status': batch.status,
                    'created_at': batch.created_at.isoformat(),
                    'processed_at': batch.processed_at.isoformat() if batch.processed_at else None,
                })
            
            return batches
            
        except Exception as e:
            logger.error(f"Error fetching settlement batches: {str(e)}")
            raise


class SettlementReportService:
    """
    Service for generating settlement reports
    Single Responsibility: Report generation
    """
    
    def __init__(self):
        self.report_model = SettlementReport
        self.batch_model = SettlementBatch
        self.detail_model = SettlementDetail
    
    def generate_settlement_report(self, batch_id: str, report_type: str, user=None) -> SettlementReport:
        """
        Generate a settlement report for a batch
        """
        try:
            batch = self.batch_model.objects.get(batch_id=batch_id)
            
            # Generate report content
            report_content = self.generate_report_content(batch, report_type)
            
            # Create report record
            report = self.report_model.objects.create(
                batch=batch,
                report_type=report_type,
                report_date=timezone.now().date(),
                generated_by=user
            )
            
            # TODO: Save report to S3 or file system
            # For now, we'll store the path
            report.file_path = f"reports/settlement_{batch_id}_{report_type}_{report.report_date}.csv"
            report.save()
            
            logger.info(f"Settlement report {report.report_id} generated")
            
            return report
            
        except self.batch_model.DoesNotExist:
            raise ValueError(f"Settlement batch {batch_id} not found")
        except Exception as e:
            logger.error(f"Error generating settlement report: {str(e)}")
            raise
    
    def generate_report_content(self, batch: SettlementBatch, report_type: str) -> str:
        """
        Generate CSV content for the report
        """
        try:
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write headers
            writer.writerow([
                'Settlement ID', 'Transaction ID', 'Client Code',
                'Transaction Amount', 'Processing Fee', 'GST',
                'Net Amount', 'Status', 'UTR Number',
                'Settlement Date'
            ])
            
            # Write settlement details
            for detail in batch.settlements.all():
                writer.writerow([
                    detail.settlement_id,
                    detail.txn_id,
                    detail.client_code,
                    detail.transaction_amount,
                    detail.processing_fee,
                    detail.gst_amount,
                    detail.net_amount,
                    detail.settlement_status,
                    detail.utr_number,
                    detail.settlement_date
                ])
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error generating report content: {str(e)}")
            raise
    
    def get_settlement_reports(self, batch_id: str = None) -> List[Dict[str, Any]]:
        """
        Get list of settlement reports
        """
        try:
            queryset = self.report_model.objects.all()
            
            if batch_id:
                queryset = queryset.filter(batch__batch_id=batch_id)
            
            reports = []
            for report in queryset[:50]:
                reports.append({
                    'report_id': str(report.report_id),
                    'batch_id': str(report.batch.batch_id),
                    'report_type': report.report_type,
                    'report_date': report.report_date.isoformat(),
                    'file_path': report.file_path,
                    'generated_at': report.generated_at.isoformat(),
                    'generated_by': report.generated_by.username if report.generated_by else None,
                })
            
            return reports
            
        except Exception as e:
            logger.error(f"Error fetching settlement reports: {str(e)}")
            raise


class SettlementReconciliationService:
    """
    Service for settlement reconciliation
    Single Responsibility: Reconciliation management
    """
    
    def __init__(self):
        self.reconciliation_model = SettlementReconciliation
        self.batch_model = SettlementBatch
    
    @transaction.atomic
    def create_reconciliation(self, batch_id: str, bank_amount: Decimal, user=None) -> SettlementReconciliation:
        """
        Create a reconciliation record for a batch
        """
        try:
            batch = self.batch_model.objects.get(batch_id=batch_id)
            
            # Get system amount
            system_amount = batch.net_settlement_amount
            
            # Create reconciliation
            reconciliation = self.reconciliation_model.objects.create(
                batch=batch,
                bank_statement_amount=bank_amount,
                system_amount=system_amount,
                difference_amount=bank_amount - system_amount,
                reconciliation_status='PENDING' if bank_amount != system_amount else 'MATCHED',
                reconciled_by=user
            )
            
            if reconciliation.reconciliation_status == 'MATCHED':
                reconciliation.reconciled_at = timezone.now()
                reconciliation.save()
            
            logger.info(f"Reconciliation {reconciliation.reconciliation_id} created")
            
            return reconciliation
            
        except self.batch_model.DoesNotExist:
            raise ValueError(f"Settlement batch {batch_id} not found")
        except Exception as e:
            logger.error(f"Error creating reconciliation: {str(e)}")
            raise
    
    def update_reconciliation_status(self, reconciliation_id: str, status: str, remarks: str = None, user=None) -> SettlementReconciliation:
        """
        Update reconciliation status
        """
        try:
            reconciliation = self.reconciliation_model.objects.get(reconciliation_id=reconciliation_id)
            
            reconciliation.reconciliation_status = status
            if remarks:
                reconciliation.remarks = remarks
            
            if status == 'RESOLVED':
                reconciliation.reconciled_at = timezone.now()
                reconciliation.reconciled_by = user
            
            reconciliation.save()
            
            logger.info(f"Reconciliation {reconciliation_id} updated to {status}")
            
            return reconciliation
            
        except self.reconciliation_model.DoesNotExist:
            raise ValueError(f"Reconciliation {reconciliation_id} not found")
        except Exception as e:
            logger.error(f"Error updating reconciliation: {str(e)}")
            raise
    
    def get_pending_reconciliations(self) -> List[Dict[str, Any]]:
        """
        Get all pending reconciliations
        """
        try:
            reconciliations = self.reconciliation_model.objects.filter(
                reconciliation_status__in=['PENDING', 'MISMATCHED', 'INVESTIGATING']
            ).order_by('-created_at')
            
            result = []
            for recon in reconciliations:
                result.append({
                    'reconciliation_id': str(recon.reconciliation_id),
                    'batch_id': str(recon.batch.batch_id),
                    'batch_date': recon.batch.batch_date.isoformat(),
                    'bank_amount': float(recon.bank_statement_amount),
                    'system_amount': float(recon.system_amount),
                    'difference': float(recon.difference_amount),
                    'status': recon.reconciliation_status,
                    'created_at': recon.created_at.isoformat(),
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching pending reconciliations: {str(e)}")
            raise


class SettlementAnalyticsService:
    """
    Service for settlement analytics
    Single Responsibility: Analytics generation
    """
    
    def __init__(self):
        self.batch_model = SettlementBatch
        self.detail_model = SettlementDetail
        self.config_model = SettlementConfiguration
    
    def get_settlement_statistics(self, date_range: str = '30d') -> Dict[str, Any]:
        """
        Get settlement statistics for dashboard
        """
        try:
            # Calculate date range
            end_date = timezone.now().date()
            if date_range == '7d':
                start_date = end_date - timedelta(days=7)
            elif date_range == '30d':
                start_date = end_date - timedelta(days=30)
            else:
                start_date = end_date - timedelta(days=30)
            
            # Get batches in range
            batches = self.batch_model.objects.filter(
                batch_date__range=[start_date, end_date]
            )
            
            # Calculate statistics
            stats = batches.aggregate(
                total_batches=Count('batch_id'),
                total_amount_settled=Sum('net_settlement_amount'),
                total_fees_collected=Sum('processing_fee'),
                total_gst_collected=Sum('gst_amount'),
                avg_batch_amount=Avg('total_amount'),
                completed_batches=Count('batch_id', filter=Q(status='COMPLETED')),
                pending_batches=Count('batch_id', filter=Q(status='PENDING')),
            )
            
            # Calculate success rate
            total = stats['total_batches'] or 1
            success_rate = (stats['completed_batches'] / total * 100) if total > 0 else 0
            
            return {
                'total_batches': stats['total_batches'] or 0,
                'total_amount_settled': float(stats['total_amount_settled'] or 0),
                'total_fees_collected': float(stats['total_fees_collected'] or 0),
                'total_gst_collected': float(stats['total_gst_collected'] or 0),
                'average_batch_amount': float(stats['avg_batch_amount'] or 0),
                'completed_batches': stats['completed_batches'] or 0,
                'pending_batches': stats['pending_batches'] or 0,
                'success_rate': round(success_rate, 2),
                'date_range': date_range,
            }
            
        except Exception as e:
            logger.error(f"Error calculating settlement statistics: {str(e)}")
            raise
    
    def get_client_settlement_summary(self, client_code: str, days: int = 30) -> Dict[str, Any]:
        """
        Get settlement summary for a specific client
        """
        try:
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Get client settlements
            settlements = self.detail_model.objects.filter(
                client_code=client_code,
                created_at__date__range=[start_date, end_date]
            )
            
            # Calculate summary
            summary = settlements.aggregate(
                total_transactions=Count('settlement_id'),
                total_settled_amount=Sum('net_amount'),
                total_fees_paid=Sum('processing_fee'),
                total_gst_paid=Sum('gst_amount'),
                settled_count=Count('settlement_id', filter=Q(settlement_status='SETTLED')),
                pending_count=Count('settlement_id', filter=Q(settlement_status='PENDING')),
            )
            
            # Get configuration
            config = self.config_model.objects.filter(client_code=client_code).first()
            
            return {
                'client_code': client_code,
                'total_transactions': summary['total_transactions'] or 0,
                'total_settled_amount': float(summary['total_settled_amount'] or 0),
                'total_fees_paid': float(summary['total_fees_paid'] or 0),
                'total_gst_paid': float(summary['total_gst_paid'] or 0),
                'settled_count': summary['settled_count'] or 0,
                'pending_count': summary['pending_count'] or 0,
                'settlement_cycle': config.settlement_cycle if config else 'T+1',
                'auto_settle': config.auto_settle if config else True,
            }
            
        except Exception as e:
            logger.error(f"Error calculating client settlement summary: {str(e)}")
            raise