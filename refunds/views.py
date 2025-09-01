from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Sum, Count, Avg
from django.db import transaction as db_transaction
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
import logging

logger = logging.getLogger(__name__)
from .models import (
    RefundRequestFromClient, RefundApprovalWorkflow,
    RefundConfiguration, RefundBatch, RefundBatchItem,
    RefundSettlementAdjustment, TransactionDetail
)
from .serializers import (
    RefundRequestSerializer, RefundApprovalSerializer,
    RefundConfigurationSerializer, RefundBatchSerializer,
    CreateRefundSerializer, ApproveRefundSerializer,
    RefundStatusSerializer, RefundReportSerializer,
    RefundTrackingSerializer
)

class RefundViewSet(viewsets.ModelViewSet):
    queryset = RefundRequestFromClient.objects.all()
    serializer_class = RefundRequestSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filters
        status_filter = self.request.query_params.get('status')
        client_id = self.request.query_params.get('client_id')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        if date_from:
            queryset = queryset.filter(refund_init_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(refund_init_date__lte=date_to)
        
        # Filter by virtual status property
        if status_filter:
            if status_filter == 'COMPLETED':
                queryset = queryset.filter(refund_complete_date__isnull=False)
            elif status_filter == 'PROCESSING':
                queryset = queryset.filter(refund_init_date__isnull=False, refund_complete_date__isnull=True)
            elif status_filter == 'PENDING':
                queryset = queryset.filter(refund_init_date__isnull=True)
        
        return queryset.order_by('-refund_id')
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get refund dashboard statistics"""
        
        # Overall statistics
        all_refunds = RefundRequestFromClient.objects.all()
        
        # Count by status
        completed = all_refunds.filter(refund_complete_date__isnull=False).count()
        processing = all_refunds.filter(refund_init_date__isnull=False, refund_complete_date__isnull=True).count()
        pending = all_refunds.filter(refund_init_date__isnull=True).count()
        
        # Calculate amounts
        total_amount_refunded = 0
        pending_amount = 0
        
        for refund in all_refunds:
            try:
                amount = float(refund.amount) if refund.amount else 0
                if refund.refund_complete_date:
                    total_amount_refunded += amount
                else:
                    pending_amount += amount
            except:
                pass
        
        # Calculate average processing time
        completed_refunds = all_refunds.filter(
            refund_complete_date__isnull=False,
            refund_init_date__isnull=False
        )
        
        avg_time = 0
        if completed_refunds.exists():
            total_hours = 0
            for refund in completed_refunds[:100]:  # Sample
                if refund.refund_init_date and refund.refund_complete_date:
                    time_diff = refund.refund_complete_date - refund.refund_init_date
                    total_hours += time_diff.total_seconds() / 3600
            avg_time = total_hours / min(len(completed_refunds), 100) if completed_refunds else 0
        
        dashboard_data = {
            'total_requests': all_refunds.count(),
            'pending_approval': pending,
            'processing': processing,
            'completed': completed,
            'rejected': 0,  # We don't have rejected status in existing table
            'total_amount_refunded': total_amount_refunded,
            'pending_amount': pending_amount,
            'average_processing_time_hours': round(avg_time, 2)
        }
        
        serializer = RefundStatusSerializer(dashboard_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def initiate(self, request):
        """Initiate a new refund request"""
        
        serializer = CreateRefundSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        with db_transaction.atomic():
            # Get transaction
            txn = TransactionDetail.objects.get(
                txn_id=serializer.validated_data['txn_id']
            )
            
            # Create refund request in existing table
            refund = RefundRequestFromClient.objects.create(
                sp_txn_id=txn.txn_id,
                client_id=str(txn.client_id),
                client_code=f"CLIENT_{txn.client_id}",
                client_txn_id=txn.txn_id,
                amount=str(serializer.validated_data['refund_amount']),
                message=serializer.validated_data['refund_reason'],
                refund_init_date=timezone.now(),
                login_id=request.user.id if hasattr(request.user, 'id') else None
            )
            
            # Update transaction refund fields
            txn.refund_status_code = 'INITIATED'
            txn.refund_initiated_on = timezone.now()
            txn.refund_amount = float(serializer.validated_data['refund_amount'])
            txn.refund_reason = serializer.validated_data['refund_reason']
            txn.refund_request_from = request.user.username
            txn.refund_track_id = f"REF{refund.refund_id:06d}"
            txn.save()
            
            # Create workflow entry
            RefundApprovalWorkflow.objects.create(
                refund_id=refund.refund_id,
                stage='INITIATED',
                action='INITIATE',
                action_by=request.user.username,
                comments=f"Refund initiated for {serializer.validated_data['refund_reason']}"
            )
            
            # Check auto-approval
            config = RefundConfiguration.objects.filter(client_id=txn.client_id).first()
            if config and config.auto_approve_threshold > 0:
                if Decimal(str(serializer.validated_data['refund_amount'])) <= config.auto_approve_threshold:
                    # Auto-approve small refunds
                    RefundApprovalWorkflow.objects.create(
                        refund_id=refund.refund_id,
                        stage='L1_APPROVAL',
                        action='APPROVE',
                        action_by='SYSTEM',
                        comments='Auto-approved due to threshold'
                    )
                    
                    # Trigger processing
                    self.process_refund(refund)
        
        return Response({
            'status': 'success',
            'refund_id': refund.refund_id,
            'refund_track_id': txn.refund_track_id,
            'message': 'Refund request initiated successfully'
        })
    
    @action(detail=False, methods=['post'])
    def approve(self, request):
        """Approve or reject refund request"""
        
        serializer = ApproveRefundSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            refund = RefundRequestFromClient.objects.get(
                refund_id=serializer.validated_data['refund_id']
            )
            
            # Check if already completed
            if refund.refund_complete_date:
                return Response(
                    {'error': 'Refund already completed'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            action = serializer.validated_data['action']
            comments = serializer.validated_data.get('comments', '')
            
            # Get current workflow stage
            last_workflow = RefundApprovalWorkflow.objects.filter(
                refund_id=refund.refund_id
            ).order_by('-workflow_id').first()
            
            # Current stage should be the next_stage from the last workflow, or INITIATED if no workflows
            if last_workflow and last_workflow.next_stage:
                current_stage = last_workflow.next_stage
            elif last_workflow:
                current_stage = last_workflow.stage
            else:
                current_stage = 'INITIATED'
            
            # Determine next stage
            if action == 'APPROVE':
                if current_stage == 'INITIATED':
                    next_stage = 'L1_APPROVAL'
                elif current_stage == 'L1_APPROVAL':
                    next_stage = 'L2_APPROVAL'
                elif current_stage == 'L2_APPROVAL':
                    next_stage = 'FINANCE_APPROVAL'
                else:
                    next_stage = 'COMPLETED'
                
                # Check if all approvals complete
                try:
                    txn = TransactionDetail.objects.get(txn_id=refund.sp_txn_id)
                    config = RefundConfiguration.objects.filter(
                        client_id=txn.client_id
                    ).first()
                    
                    if config:
                        if not config.requires_l2_approval and current_stage == 'L1_APPROVAL':
                            next_stage = 'COMPLETED'
                        elif not config.requires_finance_approval and current_stage == 'L2_APPROVAL':
                            next_stage = 'COMPLETED'
                except:
                    pass
                
                if next_stage == 'COMPLETED':
                    # Start processing
                    self.process_refund(refund)
                
            elif action == 'REJECT':
                next_stage = 'REJECTED'
                
                # Update transaction
                TransactionDetail.objects.filter(txn_id=refund.sp_txn_id).update(
                    refund_status_code='REJECTED',
                    refund_message=serializer.validated_data.get('rejection_reason', '')
                )
            
            else:  # ESCALATE
                next_stage = 'ESCALATED'
            
            # Create workflow entry
            RefundApprovalWorkflow.objects.create(
                refund_id=refund.refund_id,
                stage=current_stage,
                action=action,
                action_by=request.user.username,
                comments=comments,
                next_stage=next_stage
            )
            
            return Response({
                'status': 'success',
                'message': f'Refund {action.lower()}ed successfully'
            })
            
        except RefundRequestFromClient.DoesNotExist:
            return Response(
                {'error': 'Refund request not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'])
    def batch_process(self, request):
        """Process multiple refunds as batch"""
        
        refund_ids = request.data.get('refund_ids', [])
        
        if not refund_ids:
            return Response(
                {'error': 'No refunds selected'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create batch
        batch = RefundBatch.objects.create(
            batch_reference=f"BATCH_{uuid.uuid4().hex[:8].upper()}",
            total_refunds=len(refund_ids),
            total_amount=0,
            created_by=request.user.username
        )
        
        total_amount = Decimal('0')
        
        # Add items to batch
        for refund_id in refund_ids:
            try:
                refund = RefundRequestFromClient.objects.get(
                    refund_id=refund_id,
                    refund_init_date__isnull=False,
                    refund_complete_date__isnull=True
                )
                
                amount = Decimal(refund.amount) if refund.amount else Decimal('0')
                
                RefundBatchItem.objects.create(
                    batch=batch,
                    refund_id=refund.refund_id,
                    txn_id=refund.sp_txn_id,
                    amount=amount
                )
                
                total_amount += amount
                
            except RefundRequestFromClient.DoesNotExist:
                continue
        
        batch.total_amount = total_amount
        batch.save()
        
        # Process batch (synchronously for now)
        batch.status = 'PROCESSING'
        batch.save()
        
        # Process each item
        for item in RefundBatchItem.objects.filter(batch=batch):
            try:
                refund = RefundRequestFromClient.objects.get(refund_id=item.refund_id)
                self.process_refund(refund)
                item.status = 'COMPLETED'
                item.processed_at = timezone.now()
                item.save()
            except:
                item.status = 'FAILED'
                item.save()
        
        batch.status = 'COMPLETED'
        batch.processed_at = timezone.now()
        batch.save()
        
        return Response({
            'status': 'success',
            'batch_id': batch.batch_id,
            'batch_reference': batch.batch_reference,
            'total_refunds': batch.total_refunds,
            'total_amount': float(batch.total_amount)
        })
    
    @action(detail=True, methods=['get'])
    def workflow(self, request, pk=None):
        """Get refund workflow history"""
        
        workflows = RefundApprovalWorkflow.objects.filter(
            refund_id=pk
        ).order_by('workflow_id')
        
        serializer = RefundApprovalSerializer(workflows, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def track(self, request, pk=None):
        """Track refund status"""
        
        try:
            refund = self.get_object()
            
            # Get transaction details
            try:
                txn = TransactionDetail.objects.get(txn_id=refund.sp_txn_id)
                track_id = txn.refund_track_id or f"REF{refund.refund_id:06d}"
            except:
                track_id = f"REF{refund.refund_id:06d}"
            
            tracking_data = {
                'refund_id': refund.refund_id,
                'track_id': track_id,
                'txn_id': refund.sp_txn_id,
                'amount': float(refund.amount) if refund.amount else 0,
                'status': refund.status,
                'request_date': refund.refund_init_date,
                'approved_date': refund.refund_complete_date,
                'pg_refund_id': refund.refunded_bank_ref_id,
                'pg_status': 'COMPLETED' if refund.refund_complete_date else 'PROCESSING',
                'timeline': []
            }
            
            # Build timeline
            workflows = RefundApprovalWorkflow.objects.filter(
                refund_id=refund.refund_id
            ).order_by('workflow_id')
            
            for workflow in workflows:
                tracking_data['timeline'].append({
                    'stage': workflow.stage,
                    'action': workflow.action,
                    'by': workflow.action_by,
                    'date': workflow.action_date,
                    'comments': workflow.comments
                })
            
            serializer = RefundTrackingSerializer(tracking_data)
            return Response(serializer.data)
            
        except RefundRequestFromClient.DoesNotExist:
            return Response(
                {'error': 'Refund not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def configurations(self, request):
        """Get refund configurations"""
        
        configs = RefundConfiguration.objects.all()
        serializer = RefundConfigurationSerializer(configs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def configure(self, request):
        """Create or update refund configuration"""
        
        client_id = request.data.get('client_id')
        if not client_id:
            return Response(
                {'error': 'client_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        config, created = RefundConfiguration.objects.update_or_create(
            client_id=client_id,
            defaults=request.data
        )
        
        serializer = RefundConfigurationSerializer(config)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def report(self, request):
        """Get refund report"""
        
        days = int(request.query_params.get('days', 30))
        
        report_data = []
        for i in range(days):
            date = timezone.now().date() - timedelta(days=i)
            
            # Get refunds for this date
            day_refunds = RefundRequestFromClient.objects.filter(
                refund_init_date__date=date
            )
            
            completed = day_refunds.filter(refund_complete_date__isnull=False).count()
            
            total_amount = 0
            for refund in day_refunds.filter(refund_complete_date__isnull=False):
                try:
                    total_amount += float(refund.amount) if refund.amount else 0
                except:
                    pass
            
            report_data.append({
                'date': date,
                'requests_count': day_refunds.count(),
                'approved_count': completed,
                'rejected_count': 0,
                'completed_count': completed,
                'total_amount': total_amount
            })
        
        return Response(report_data)
    
    def process_refund(self, refund):
        """Process approved refund"""
        
        # Update transaction
        try:
            txn = TransactionDetail.objects.get(txn_id=refund.sp_txn_id)
            txn.refund_status_code = 'PROCESSING'
            txn.refund_process_on = timezone.now()
            txn.save()
            
            # Adjust settlement if already settled
            if txn.is_settled:
                RefundSettlementAdjustment.objects.create(
                    refund_id=refund.refund_id,
                    txn_id=refund.sp_txn_id,
                    original_settlement_amount=txn.settlement_amount or txn.paid_amount,
                    refund_amount=Decimal(refund.amount) if refund.amount else Decimal('0'),
                    adjusted_settlement_amount=(txn.settlement_amount or txn.paid_amount) - Decimal(refund.amount if refund.amount else '0'),
                    adjustment_type='DEBIT',
                    settlement_date=txn.settlement_date.date() if txn.settlement_date else timezone.now().date()
                )
        except:
            pass
        
        # In production, this would trigger actual gateway refund
        # For now, we'll simulate completion
        refund.refund_complete_date = timezone.now()
        refund.refunded_bank_ref_id = f"BANK_REF_{uuid.uuid4().hex[:8].upper()}"
        refund.save()
        
        # IMPORTANT: Update transaction to mark refund as completed
        try:
            txn = TransactionDetail.objects.get(txn_id=refund.sp_txn_id)
            txn.refund_status_code = 'COMPLETED'
            txn.refunded_date = timezone.now()
            txn.refunded_amount = float(refund.amount) if refund.amount else 0
            txn.refund_message = f"Refund completed - Bank Ref: {refund.refunded_bank_ref_id}"
            txn.save()
        except Exception as e:
            logger.error(f"Failed to update transaction refund completion: {str(e)}")
