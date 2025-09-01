from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Sum, Count, Avg, F
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import logging

from .models import FeeConfiguration, FeeCalculationLog, PromotionalFees, FeeReconciliation
from .serializers import (
    FeeConfigurationSerializer, FeeCalculationLogSerializer,
    PromotionalFeesSerializer, FeeReconciliationSerializer,
    FeeCalculatorSerializer, BulkFeeUpdateSerializer, FeeComparisonSerializer
)

logger = logging.getLogger(__name__)


class FeeConfigurationViewSet(viewsets.ModelViewSet):
    serializer_class = FeeConfigurationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = FeeConfiguration.objects.all().order_by('-created_at')
        
        # Filters
        client_id = self.request.query_params.get('client_id')
        fee_type = self.request.query_params.get('fee_type')
        is_active = self.request.query_params.get('is_active')
        
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        if fee_type:
            queryset = queryset.filter(fee_type=fee_type)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user.username)
    
    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """Bulk update fee configurations"""
        serializer = BulkFeeUpdateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        updated_count = 0
        
        for client_id in data['client_ids']:
            configs = FeeConfiguration.objects.filter(
                client_id=client_id,
                fee_type=data['fee_type'],
                is_active=True
            )
            
            for config in configs:
                # Deactivate old config
                config.is_active = False
                config.effective_until = timezone.now()
                config.save()
                
                # Create new config with updates
                new_config = FeeConfiguration.objects.create(
                    client_id=client_id,
                    fee_name=config.fee_name,
                    fee_type=data['fee_type'],
                    fee_structure=config.fee_structure,
                    base_rate=data['updates'].get('base_rate', config.base_rate),
                    minimum_fee=data['updates'].get('minimum_fee', config.minimum_fee),
                    maximum_fee=data['updates'].get('maximum_fee', config.maximum_fee),
                    tier_rates=data['updates'].get('tier_rates', config.tier_rates),
                    volume_slabs=data['updates'].get('volume_slabs', config.volume_slabs),
                    payment_method_rates=data['updates'].get('payment_method_rates', config.payment_method_rates),
                    conditions=config.conditions,
                    effective_from=data['effective_from'],
                    created_by=self.request.user.username
                )
                updated_count += 1
        
        return Response({
            'message': f'Updated {updated_count} fee configurations',
            'reason': data['reason']
        })
    
    @action(detail=False, methods=['post'])
    def compare_fees(self, request):
        """Compare fees across multiple clients"""
        serializer = FeeComparisonSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        comparison_date = data.get('comparison_date', timezone.now())
        fee_types = data.get('fee_types', ['TRANSACTION', 'PROCESSING', 'SETTLEMENT'])
        
        comparison_data = []
        
        for client_id in data['client_ids']:
            client_fees = {}
            
            for fee_type in fee_types:
                config = FeeConfiguration.objects.filter(
                    client_id=client_id,
                    fee_type=fee_type,
                    effective_from__lte=comparison_date,
                    is_active=True
                ).filter(
                    Q(effective_until__gte=comparison_date) | Q(effective_until__isnull=True)
                ).first()
                
                if config:
                    client_fees[fee_type] = {
                        'base_rate': float(config.base_rate),
                        'structure': config.fee_structure,
                        'minimum_fee': float(config.minimum_fee),
                        'maximum_fee': float(config.maximum_fee) if config.maximum_fee else None
                    }
                else:
                    client_fees[fee_type] = None
            
            comparison_data.append({
                'client_id': client_id,
                'fees': client_fees
            })
        
        return Response(comparison_data)
    
    @action(detail=True, methods=['post'])
    def clone_configuration(self, request, pk=None):
        """Clone a fee configuration for another client"""
        source_config = self.get_object()
        target_client_id = request.data.get('target_client_id')
        
        if not target_client_id:
            return Response(
                {'error': 'target_client_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if similar config already exists
        existing = FeeConfiguration.objects.filter(
            client_id=target_client_id,
            fee_type=source_config.fee_type,
            is_active=True
        ).exists()
        
        if existing:
            return Response(
                {'error': 'Active configuration already exists for target client'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Clone the configuration
        cloned_config = FeeConfiguration.objects.create(
            client_id=target_client_id,
            fee_name=source_config.fee_name,
            fee_type=source_config.fee_type,
            fee_structure=source_config.fee_structure,
            base_rate=source_config.base_rate,
            minimum_fee=source_config.minimum_fee,
            maximum_fee=source_config.maximum_fee,
            tier_rates=source_config.tier_rates,
            volume_slabs=source_config.volume_slabs,
            payment_method_rates=source_config.payment_method_rates,
            conditions=source_config.conditions,
            effective_from=timezone.now(),
            created_by=self.request.user.username
        )
        
        serializer = self.get_serializer(cloned_config)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class FeeCalculationViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def calculate(self, request):
        """Calculate fee for a transaction"""
        serializer = FeeCalculatorSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        # Find applicable fee configuration
        config = FeeConfiguration.objects.filter(
            client_id=data['client_id'],
            fee_type=data['fee_type'],
            is_active=True,
            effective_from__lte=timezone.now()
        ).filter(
            Q(effective_until__gte=timezone.now()) | Q(effective_until__isnull=True)
        ).first()
        
        if not config:
            return Response(
                {'error': 'No active fee configuration found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Calculate base fee
        try:
            calculated_fee = config.calculate_fee(
                data['transaction_amount'],
                payment_method=data.get('payment_method'),
                volume_data=data.get('volume_data')
            )
        except Exception as e:
            return Response(
                {'error': f'Fee calculation failed: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        discount_amount = Decimal('0')
        promo_details = None
        
        # Apply promotional discount if promo code provided
        if data.get('promo_code'):
            promo = PromotionalFees.objects.filter(
                promo_code=data['promo_code'].upper(),
                client_id=data['client_id'],
                status='ACTIVE'
            ).first()
            
            if promo and promo.is_valid:
                try:
                    discount_amount = promo.apply_discount(
                        calculated_fee,
                        data['transaction_amount']
                    )
                    promo_details = {
                        'promo_code': promo.promo_code,
                        'discount_type': promo.discount_type,
                        'discount_amount': float(discount_amount)
                    }
                except ValueError as e:
                    promo_details = {'error': str(e)}
        
        final_fee = calculated_fee - discount_amount
        
        # Log the calculation
        log = FeeCalculationLog.objects.create(
            transaction_id=request.data.get('transaction_id', f"CALC_{timezone.now().timestamp()}"),
            fee_id=config.fee_id,
            client_id=data['client_id'],
            transaction_amount=data['transaction_amount'],
            payment_method=data.get('payment_method', 'UNKNOWN'),
            calculated_amount=calculated_fee,
            calculation_method='AUTO',
            calculation_details={
                'fee_structure': config.fee_structure,
                'base_rate': float(config.base_rate),
                'volume_data': data.get('volume_data')
            },
            promo_code_applied=data.get('promo_code'),
            discount_amount=discount_amount,
            final_fee_amount=final_fee,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )
        
        return Response({
            'calculation_id': log.calc_id,
            'transaction_amount': float(data['transaction_amount']),
            'calculated_fee': float(calculated_fee),
            'discount_amount': float(discount_amount),
            'final_fee': float(final_fee),
            'total_amount': float(data['transaction_amount'] + final_fee),
            'fee_configuration': {
                'fee_type': config.fee_type,
                'fee_structure': config.fee_structure,
                'base_rate': float(config.base_rate)
            },
            'promotional_details': promo_details
        })
    
    @action(detail=False, methods=['post'])
    def preview_with_promotion(self, request):
        """Preview fee calculation with promotional code"""
        client_id = request.data.get('client_id')
        promo_code = request.data.get('promo_code')
        test_amounts = request.data.get('test_amounts', [100, 1000, 5000, 10000])
        
        if not client_id or not promo_code:
            return Response(
                {'error': 'client_id and promo_code are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        promo = PromotionalFees.objects.filter(
            promo_code=promo_code.upper(),
            client_id=client_id,
            status='ACTIVE'
        ).first()
        
        if not promo or not promo.is_valid:
            return Response(
                {'error': 'Invalid or expired promotional code'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        config = FeeConfiguration.objects.filter(
            client_id=client_id,
            fee_type='TRANSACTION',
            is_active=True
        ).first()
        
        if not config:
            return Response(
                {'error': 'No active fee configuration found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        preview = []
        for amount in test_amounts:
            calculated_fee = config.calculate_fee(amount)
            discount = promo.apply_discount(calculated_fee, amount)
            final_fee = calculated_fee - discount
            
            preview.append({
                'amount': amount,
                'calculated_fee': float(calculated_fee),
                'discount': float(discount),
                'final_fee': float(final_fee),
                'total': float(amount + final_fee),
                'savings': float(discount)
            })
        
        return Response({
            'promo_code': promo.promo_code,
            'promo_name': promo.promo_name,
            'discount_type': promo.discount_type,
            'discount_value': float(promo.discount_value),
            'preview': preview
        })


class FeeCalculationLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = FeeCalculationLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = FeeCalculationLog.objects.all().order_by('-created_at')
        
        # Filters
        client_id = self.request.query_params.get('client_id')
        transaction_id = self.request.query_params.get('transaction_id')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        if transaction_id:
            queryset = queryset.filter(transaction_id=transaction_id)
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get fee calculation statistics"""
        client_id = request.query_params.get('client_id')
        period = request.query_params.get('period', '7')  # Days
        
        start_date = timezone.now() - timedelta(days=int(period))
        
        queryset = FeeCalculationLog.objects.filter(created_at__gte=start_date)
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        
        stats = queryset.aggregate(
            total_calculations=Count('calc_id'),
            total_transaction_amount=Sum('transaction_amount'),
            total_fees_calculated=Sum('calculated_amount'),
            total_discounts=Sum('discount_amount'),
            total_final_fees=Sum('final_fee_amount'),
            avg_fee_rate=Avg(F('final_fee_amount') / F('transaction_amount') * 100)
        )
        
        # Calculate by payment method
        by_payment_method = queryset.values('payment_method').annotate(
            count=Count('calc_id'),
            total_fees=Sum('final_fee_amount')
        ).order_by('-total_fees')[:5]
        
        # Calculate by calculation method
        by_calc_method = queryset.values('calculation_method').annotate(
            count=Count('calc_id'),
            total_fees=Sum('final_fee_amount')
        )
        
        return Response({
            'period_days': period,
            'statistics': stats,
            'by_payment_method': list(by_payment_method),
            'by_calculation_method': list(by_calc_method)
        })


class PromotionalFeesViewSet(viewsets.ModelViewSet):
    serializer_class = PromotionalFeesSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = PromotionalFees.objects.all().order_by('-created_at')
        
        # Filters
        client_id = self.request.query_params.get('client_id')
        status_filter = self.request.query_params.get('status')
        active_only = self.request.query_params.get('active_only')
        
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if active_only and active_only.lower() == 'true':
            now = timezone.now()
            queryset = queryset.filter(
                status='ACTIVE',
                valid_from__lte=now,
                valid_until__gte=now,
                used_count__lt=F('usage_limit')
            )
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user.username)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a promotional code"""
        promo = self.get_object()
        promo.status = 'ACTIVE'
        promo.save()
        
        return Response({'message': f'Promotional code {promo.promo_code} activated'})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a promotional code"""
        promo = self.get_object()
        promo.status = 'INACTIVE'
        promo.save()
        
        return Response({'message': f'Promotional code {promo.promo_code} deactivated'})
    
    @action(detail=True, methods=['post'])
    def extend_validity(self, request, pk=None):
        """Extend validity period of a promotional code"""
        promo = self.get_object()
        days_to_extend = request.data.get('days', 30)
        
        promo.valid_until = promo.valid_until + timedelta(days=days_to_extend)
        promo.save()
        
        return Response({
            'message': f'Validity extended by {days_to_extend} days',
            'new_valid_until': promo.valid_until
        })
    
    @action(detail=False, methods=['get'])
    def validate_code(self, request):
        """Validate a promotional code"""
        promo_code = request.query_params.get('code')
        client_id = request.query_params.get('client_id')
        
        if not promo_code or not client_id:
            return Response(
                {'error': 'code and client_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        promo = PromotionalFees.objects.filter(
            promo_code=promo_code.upper(),
            client_id=client_id
        ).first()
        
        if not promo:
            return Response(
                {'valid': False, 'reason': 'Code not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not promo.is_valid:
            reasons = []
            now = timezone.now()
            
            if promo.status != 'ACTIVE':
                reasons.append(f'Code is {promo.status}')
            if promo.valid_from > now:
                reasons.append('Code not yet valid')
            if promo.valid_until < now:
                reasons.append('Code has expired')
            if promo.used_count >= promo.usage_limit:
                reasons.append('Usage limit reached')
            
            return Response({
                'valid': False,
                'reasons': reasons
            })
        
        return Response({
            'valid': True,
            'promo_code': promo.promo_code,
            'promo_name': promo.promo_name,
            'discount_type': promo.discount_type,
            'discount_value': float(promo.discount_value),
            'usage_remaining': promo.usage_limit - promo.used_count
        })


class FeeReconciliationViewSet(viewsets.ModelViewSet):
    serializer_class = FeeReconciliationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = FeeReconciliation.objects.all().order_by('-created_at')
        
        # Filters
        client_id = self.request.query_params.get('client_id')
        period = self.request.query_params.get('period')
        status_filter = self.request.query_params.get('status')
        
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        if period:
            queryset = queryset.filter(period=period)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def start_reconciliation(self, request, pk=None):
        """Start the reconciliation process"""
        recon = self.get_object()
        
        if recon.status != 'PENDING':
            return Response(
                {'error': 'Reconciliation already started'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        recon.status = 'IN_PROGRESS'
        recon.save()
        
        # Calculate fees from logs
        period_start, period_end = self._get_period_dates(recon.period)
        
        fee_logs = FeeCalculationLog.objects.filter(
            client_id=recon.client_id,
            created_at__gte=period_start,
            created_at__lte=period_end
        )
        
        aggregated = fee_logs.aggregate(
            total_transactions=Count('calc_id'),
            total_transaction_amount=Sum('transaction_amount'),
            calculated_fees=Sum('calculated_amount'),
            total_discounts=Sum('discount_amount'),
            total_final_fees=Sum('final_fee_amount')
        )
        
        recon.total_transactions = aggregated['total_transactions'] or 0
        recon.total_transaction_amount = aggregated['total_transaction_amount'] or 0
        recon.calculated_fees = aggregated['total_final_fees'] or 0
        
        # Calculate fee breakdown by type
        fee_breakdown = fee_logs.values('fee_id').annotate(
            total=Sum('final_fee_amount')
        )
        
        breakdown_dict = {}
        for item in fee_breakdown:
            try:
                config = FeeConfiguration.objects.get(fee_id=item['fee_id'])
                breakdown_dict[config.fee_type] = float(item['total'])
            except FeeConfiguration.DoesNotExist:
                pass
        
        recon.fee_breakdown = breakdown_dict
        
        # Calculate variance
        recon.calculate_variance()
        
        return Response({
            'message': 'Reconciliation completed',
            'status': recon.status,
            'variance': float(recon.variance),
            'variance_percentage': float(recon.variance_percentage)
        })
    
    @action(detail=True, methods=['post'])
    def mark_resolved(self, request, pk=None):
        """Mark reconciliation as resolved"""
        recon = self.get_object()
        notes = request.data.get('notes', '')
        
        recon.status = 'RESOLVED'
        recon.reconciled_at = timezone.now()
        recon.reconciled_by = self.request.user.username
        recon.notes = notes
        recon.save()
        
        return Response({'message': 'Reconciliation marked as resolved'})
    
    def _get_period_dates(self, period):
        """Get start and end dates for a period"""
        # Period format: "2024-01" for month, "2024-Q1" for quarter
        if '-Q' in period:
            year, quarter = period.split('-Q')
            year = int(year)
            quarter = int(quarter)
            
            quarter_starts = {
                1: datetime(year, 1, 1),
                2: datetime(year, 4, 1),
                3: datetime(year, 7, 1),
                4: datetime(year, 10, 1)
            }
            
            start = quarter_starts[quarter]
            if quarter == 4:
                end = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end = quarter_starts[quarter + 1] - timedelta(days=1)
        else:
            # Monthly period
            year, month = period.split('-')
            year = int(year)
            month = int(month)
            
            start = datetime(year, month, 1)
            if month == 12:
                end = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end = datetime(year, month + 1, 1) - timedelta(days=1)
        
        return timezone.make_aware(start), timezone.make_aware(end)