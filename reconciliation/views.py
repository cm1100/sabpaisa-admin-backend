from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Sum, Count
from django.db import transaction as db_transaction
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import pandas as pd
import csv
import re
from .models import (
    TransactionDetail, TransactionReconTable,
    BankStatementUpload, BankStatementEntry,
    ReconciliationMismatch, ReconciliationRule
)
from .serializers import (
    ReconciliationStatusSerializer, TransactionReconSerializer,
    BankStatementUploadSerializer, BankStatementEntrySerializer,
    ReconciliationMismatchSerializer, ReconciliationRuleSerializer,
    ManualMatchSerializer, ReconciliationReportSerializer,
    BankStatementParseSerializer
)

class ReconciliationViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Get reconciliation dashboard summary"""
        try:
            # Overall status
            recon_stats = TransactionReconTable.objects.aggregate(
                total=Count('recon_id'),
                matched=Count('recon_id', filter=Q(recon_status='MATCHED')),
                mismatched=Count('recon_id', filter=Q(recon_status='MISMATCHED')),
                pending=Count('recon_id', filter=Q(recon_status='PENDING')),
                total_amount=Sum('transaction_amount'),
                matched_amount=Sum('transaction_amount', filter=Q(recon_status='MATCHED')),
                mismatched_amount=Sum('transaction_amount', filter=Q(recon_status='MISMATCHED'))
            )
            
            match_rate = (recon_stats['matched'] / recon_stats['total'] * 100) if recon_stats['total'] > 0 else 0
            
            status_data = {
                'total_transactions': recon_stats['total'] or 0,
                'matched': recon_stats['matched'] or 0,
                'mismatched': recon_stats['mismatched'] or 0,
                'pending': recon_stats['pending'] or 0,
                'match_rate': round(match_rate, 2),
                'total_amount': float(recon_stats['total_amount'] or 0),
                'matched_amount': float(recon_stats['matched_amount'] or 0),
                'mismatched_amount': float(recon_stats['mismatched_amount'] or 0)
            }
        except Exception as e:
            # Return empty stats if table doesn't exist yet
            status_data = {
                'total_transactions': 0,
                'matched': 0,
                'mismatched': 0,
                'pending': 0,
                'match_rate': 0.0,
                'total_amount': 0.0,
                'matched_amount': 0.0,
                'mismatched_amount': 0.0,
                'message': 'Reconciliation system initialized. Upload bank statements to begin reconciliation.'
            }
        
        return Response(status_data)
    
    @action(detail=False, methods=['post'])
    def upload_statement(self, request):
        """Upload and process bank statement"""
        file = request.FILES.get('file')
        bank_name = request.data.get('bank_name')
        statement_date = request.data.get('statement_date')
        file_format = request.data.get('format', 'CSV')
        
        if not file:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Save upload record
        upload = BankStatementUpload.objects.create(
            file_name=file.name,
            file_path=f'/tmp/{file.name}',
            bank_name=bank_name,
            statement_date=statement_date,
            uploaded_by=request.user.username,
            status='PROCESSING'
        )
        
        # Save file temporarily
        with open(f'/tmp/{file.name}', 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        
        # Parse the statement
        try:
            entries = self.parse_bank_statement(
                f'/tmp/{file.name}',
                file_format,
                upload
            )
            
            # Run auto-matching
            matched, mismatched = self.auto_match_transactions(entries)
            
            # Update upload record
            upload.total_records = len(entries)
            upload.matched_records = matched
            upload.mismatched_records = mismatched
            upload.status = 'COMPLETED'
            upload.save()
            
            return Response({
                'upload_id': upload.upload_id,
                'total_records': len(entries),
                'matched': matched,
                'mismatched': mismatched,
                'match_rate': round((matched / len(entries) * 100) if entries else 0, 2)
            })
            
        except Exception as e:
            upload.status = 'FAILED'
            upload.save()
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def pending_reconciliation(self, request):
        """Get transactions pending reconciliation"""
        try:
            date_from = request.query_params.get('date_from')
            date_to = request.query_params.get('date_to')
            
            # Get unreconciled transactions
            queryset = TransactionReconTable.objects.filter(
                recon_status__in=['PENDING', 'MISMATCHED']
            )
            
            if date_from:
                queryset = queryset.filter(created_at__gte=date_from)
            if date_to:
                queryset = queryset.filter(created_at__lte=date_to)
            
            serializer = TransactionReconSerializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            # Return empty list if table doesn't exist yet
            return Response([])
    
    @action(detail=False, methods=['get'])
    def mismatches(self, request):
        """Get reconciliation mismatches"""
        try:
            status_filter = request.query_params.get('status', 'OPEN')
            
            mismatches = ReconciliationMismatch.objects.filter(
                status=status_filter
            ).order_by('-created_at')
            
            serializer = ReconciliationMismatchSerializer(mismatches, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response([])
    
    @action(detail=False, methods=['post'])
    def manual_match(self, request):
        """Manually match a transaction with bank entry"""
        serializer = ManualMatchSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        txn_id = serializer.validated_data['txn_id']
        bank_entry_id = serializer.validated_data['bank_entry_id']
        remarks = serializer.validated_data.get('remarks', '')
        
        try:
            # Get transaction and bank entry
            recon_record = TransactionReconTable.objects.get(txn_id=txn_id)
            bank_entry = BankStatementEntry.objects.get(entry_id=bank_entry_id)
            
            # Update reconciliation record
            recon_record.recon_status = 'MATCHED'
            recon_record.bank_reference = bank_entry.reference_number
            recon_record.bank_amount = bank_entry.credit_amount or bank_entry.debit_amount
            recon_record.bank_date = bank_entry.transaction_date
            recon_record.matched_by = 'MANUAL'
            recon_record.matched_at = timezone.now()
            recon_record.remarks = remarks
            recon_record.save()
            
            # Update bank entry
            bank_entry.matched_txn_id = txn_id
            bank_entry.match_status = 'MATCHED'
            bank_entry.match_confidence = 100
            bank_entry.save()
            
            # Resolve any mismatches
            ReconciliationMismatch.objects.filter(
                Q(txn_id=txn_id) | Q(bank_entry_id=bank_entry_id)
            ).update(
                status='RESOLVED',
                resolution=f'Manually matched by {request.user.username}',
                resolved_by=request.user.username,
                resolved_at=timezone.now()
            )
            
            return Response({
                'status': 'success',
                'message': 'Transaction matched successfully'
            })
            
        except (TransactionReconTable.DoesNotExist, BankStatementEntry.DoesNotExist):
            return Response(
                {'error': 'Transaction or bank entry not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def bank_entries(self, request):
        """Get unmatched bank statement entries"""
        try:
            upload_id = request.query_params.get('upload_id')
            
            queryset = BankStatementEntry.objects.filter(
                match_status='UNMATCHED'
            )
            
            if upload_id:
                queryset = queryset.filter(upload_id=upload_id)
            
            serializer = BankStatementEntrySerializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response([])
    
    @action(detail=False, methods=['get'])
    def rules(self, request):
        """Get reconciliation rules"""
        rules = ReconciliationRule.objects.filter(
            is_active=True
        ).order_by('priority')
        
        serializer = ReconciliationRuleSerializer(rules, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def create_rule(self, request):
        """Create reconciliation rule"""
        serializer = ReconciliationRuleSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def run_reconciliation(self, request):
        """Run reconciliation for a date range"""
        date_from = request.data.get('date_from')
        date_to = request.data.get('date_to')
        
        # Get transactions in date range
        transactions = TransactionDetail.objects.filter(
            created_date__date__gte=date_from,
            created_date__date__lte=date_to,
            status='SUCCESS'
        )
        
        # Create/update reconciliation records
        created_count = 0
        for txn in transactions:
            recon, created = TransactionReconTable.objects.get_or_create(
                txn_id=txn.txn_id,
                defaults={
                    'client_id': txn.client_id,
                    'transaction_amount': txn.paid_amount,
                    'recon_status': 'PENDING'
                }
            )
            if created:
                created_count += 1
        
        # Get latest bank statement entries
        bank_entries = BankStatementEntry.objects.filter(
            transaction_date__gte=date_from,
            transaction_date__lte=date_to,
            match_status='UNMATCHED'
        )
        
        # Run auto-matching
        matched, mismatched = self.auto_match_transactions(bank_entries)
        
        return Response({
            'transactions_processed': transactions.count(),
            'reconciliation_records_created': created_count,
            'matched': matched,
            'mismatched': mismatched,
            'pending': transactions.count() - matched - mismatched
        })
    
    @action(detail=False, methods=['get'])
    def report(self, request):
        """Get reconciliation report"""
        days = int(request.query_params.get('days', 7))
        
        report_data = []
        for i in range(days):
            date = timezone.now().date() - timedelta(days=i)
            
            stats = TransactionReconTable.objects.filter(
                created_at__date=date
            ).aggregate(
                total=Count('recon_id'),
                matched=Count('recon_id', filter=Q(recon_status='MATCHED')),
                matched_amount=Sum('transaction_amount', filter=Q(recon_status='MATCHED')),
                mismatched=Count('recon_id', filter=Q(recon_status='MISMATCHED')),
                mismatched_amount=Sum('transaction_amount', filter=Q(recon_status='MISMATCHED'))
            )
            
            match_percentage = (stats['matched'] / stats['total'] * 100) if stats['total'] > 0 else 0
            
            report_data.append({
                'date': date,
                'total_transactions': stats['total'] or 0,
                'matched_count': stats['matched'] or 0,
                'matched_amount': float(stats['matched_amount'] or 0),
                'mismatched_count': stats['mismatched'] or 0,
                'mismatched_amount': float(stats['mismatched_amount'] or 0),
                'match_percentage': round(match_percentage, 2)
            })
        
        return Response(report_data)
    
    def parse_bank_statement(self, file_path, file_format, upload):
        """Parse bank statement file"""
        entries = []
        
        if file_format == 'CSV':
            # Parse CSV file
            with open(file_path, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # Adjust field mapping based on bank format
                    entry = BankStatementEntry.objects.create(
                        upload_id=upload,
                        transaction_date=self.parse_date(row.get('Date', '')),
                        value_date=self.parse_date(row.get('Value Date', row.get('Date', ''))),
                        description=row.get('Description', ''),
                        reference_number=row.get('Reference', row.get('UTR', '')),
                        debit_amount=self.parse_amount(row.get('Debit', '0')),
                        credit_amount=self.parse_amount(row.get('Credit', '0')),
                        balance=self.parse_amount(row.get('Balance', '0')),
                        transaction_type='CREDIT' if row.get('Credit') else 'DEBIT'
                    )
                    entries.append(entry)
                    
        elif file_format == 'EXCEL':
            # Parse Excel file
            df = pd.read_excel(file_path)
            for _, row in df.iterrows():
                entry = BankStatementEntry.objects.create(
                    upload_id=upload,
                    transaction_date=pd.to_datetime(row.get('Date')).date(),
                    value_date=pd.to_datetime(row.get('Value Date', row.get('Date'))).date(),
                    description=str(row.get('Description', '')),
                    reference_number=str(row.get('Reference', '')),
                    debit_amount=Decimal(str(row.get('Debit', 0) or 0)),
                    credit_amount=Decimal(str(row.get('Credit', 0) or 0)),
                    balance=Decimal(str(row.get('Balance', 0) or 0)),
                    transaction_type='CREDIT' if row.get('Credit') else 'DEBIT'
                )
                entries.append(entry)
        
        return entries
    
    def auto_match_transactions(self, bank_entries):
        """Auto-match transactions with bank entries"""
        matched_count = 0
        mismatched_count = 0
        
        # Get active matching rules
        rules = ReconciliationRule.objects.filter(
            is_active=True
        ).order_by('priority')
        
        for entry in bank_entries:
            amount = entry.credit_amount or entry.debit_amount
            
            # Try to find matching transaction
            match_found = False
            
            # Rule 1: Exact amount and reference match
            if entry.reference_number:
                recon = TransactionReconTable.objects.filter(
                    Q(bank_reference=entry.reference_number) |
                    Q(txn_id__icontains=entry.reference_number),
                    transaction_amount=amount,
                    recon_status='PENDING'
                ).first()
                
                if recon:
                    self.create_match(recon, entry, 'AUTO', 95)
                    matched_count += 1
                    match_found = True
            
            # Rule 2: Amount match within date range
            if not match_found:
                date_range_start = entry.transaction_date - timedelta(days=2)
                date_range_end = entry.transaction_date + timedelta(days=2)
                
                recon = TransactionReconTable.objects.filter(
                    transaction_amount=amount,
                    created_at__date__range=[date_range_start, date_range_end],
                    recon_status='PENDING'
                ).first()
                
                if recon:
                    self.create_match(recon, entry, 'AUTO', 75)
                    matched_count += 1
                    match_found = True
            
            # Rule 3: Fuzzy amount match (within tolerance)
            if not match_found:
                tolerance = Decimal('10.00')  # ₹10 tolerance
                
                recon = TransactionReconTable.objects.filter(
                    transaction_amount__gte=amount - tolerance,
                    transaction_amount__lte=amount + tolerance,
                    created_at__date=entry.transaction_date,
                    recon_status='PENDING'
                ).first()
                
                if recon:
                    self.create_match(recon, entry, 'AUTO', 60)
                    matched_count += 1
                    match_found = True
            
            # If no match found, create mismatch record
            if not match_found:
                ReconciliationMismatch.objects.create(
                    bank_entry_id=entry,
                    mismatch_type='MISSING_IN_SYSTEM',
                    bank_amount=amount,
                    bank_date=entry.transaction_date,
                    status='OPEN'
                )
                mismatched_count += 1
        
        # Check for transactions not in bank
        unmatched_txns = TransactionReconTable.objects.filter(
            recon_status='PENDING',
            created_at__lt=timezone.now() - timedelta(days=3)
        )
        
        for txn in unmatched_txns:
            ReconciliationMismatch.objects.create(
                txn_id=txn.txn_id,
                mismatch_type='MISSING_IN_BANK',
                system_amount=txn.transaction_amount,
                status='OPEN'
            )
            txn.recon_status = 'MISMATCHED'
            txn.save()
            mismatched_count += 1
        
        return matched_count, mismatched_count
    
    def create_match(self, recon, bank_entry, matched_by, confidence):
        """Create a match between transaction and bank entry"""
        recon.recon_status = 'MATCHED'
        recon.bank_reference = bank_entry.reference_number
        recon.bank_amount = bank_entry.credit_amount or bank_entry.debit_amount
        recon.bank_date = bank_entry.transaction_date
        recon.matched_by = matched_by
        recon.matched_at = timezone.now()
        recon.recon_date = timezone.now()
        recon.save()
        
        bank_entry.matched_txn_id = recon.txn_id
        bank_entry.match_status = 'MATCHED'
        bank_entry.match_confidence = confidence
        bank_entry.save()
        
        # Update main transaction
        TransactionDetail.objects.filter(txn_id=recon.txn_id).update(
            reconciliation_date=timezone.now()
        )
    
    def parse_date(self, date_str):
        """Parse date from various formats"""
        if not date_str:
            return None
        
        formats = ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%m/%d/%Y']
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except:
                continue
        return None
    
    def parse_amount(self, amount_str):
        """Parse amount from string"""
        if not amount_str:
            return Decimal('0')
        
        # Remove currency symbols and commas
        amount_str = re.sub(r'[₹$,]', '', str(amount_str))
        
        try:
            return Decimal(amount_str)
        except:
            return Decimal('0')
