from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Sum, Avg
from django.db import connection
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json
import csv
from django.http import HttpResponse
from .models import (
    TransactionDetail, ClientDataTable,
    AdminUserActivityLog, ComplianceAlert, RBIReportLog
)
from .serializers import (
    KYCStatusSerializer, SuspiciousTransactionSerializer,
    AuditLogSerializer, ComplianceAlertSerializer,
    ComplianceDashboardSerializer, RBIReportSerializer,
    ComplianceReviewSerializer, TransactionRiskAnalysisSerializer
)


class ComplianceViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Get compliance dashboard summary"""
        # KYC Summary
        kyc_stats = ClientDataTable.objects.aggregate(
            total=Count('client_id'),
            verified=Count('client_id', filter=Q(kyc_status='VERIFIED')),
            pending=Count('client_id', filter=Q(kyc_status='PENDING')),
            rejected=Count('client_id', filter=Q(kyc_status='REJECTED'))
        )
        
        # Check for expired KYC (older than 1 year)
        one_year_ago = timezone.now() - timedelta(days=365)
        expired_count = ClientDataTable.objects.filter(
            kyc_verified_date__lt=one_year_ago
        ).count()
        
        kyc_summary = {
            'total_clients': kyc_stats['total'],
            'verified': kyc_stats['verified'],
            'pending': kyc_stats['pending'],
            'rejected': kyc_stats['rejected'],
            'expired': expired_count,
            'verification_rate': (kyc_stats['verified'] / kyc_stats['total'] * 100) if kyc_stats['total'] > 0 else 0
        }
        
        # Risk Distribution
        risk_dist = ClientDataTable.objects.values('risk_category').annotate(
            count=Count('client_id')
        )
        risk_distribution = {item['risk_category']: item['count'] for item in risk_dist}
        
        # Recent Alerts
        recent_alerts = ComplianceAlert.objects.filter(
            status='OPEN'
        ).order_by('-detected_at')[:10]
        
        # Suspicious Transactions (basic detection)
        suspicious_txns = self.detect_suspicious_transactions()
        
        # Compliance Score (simplified calculation)
        compliance_score = self.calculate_compliance_score(kyc_summary, len(suspicious_txns))
        
        # Pending Reviews
        pending_reviews = ComplianceAlert.objects.filter(
            status__in=['OPEN', 'UNDER_REVIEW']
        ).count()
        
        dashboard_data = {
            'kyc_summary': kyc_summary,
            'risk_distribution': risk_distribution,
            'recent_alerts': ComplianceAlertSerializer(recent_alerts, many=True).data,
            'suspicious_transactions': suspicious_txns[:5],
            'compliance_score': compliance_score,
            'pending_reviews': pending_reviews
        }
        
        return Response(dashboard_data)
    
    def detect_suspicious_transactions(self):
        """Detect suspicious transactions based on patterns"""
        suspicious = []
        
        # Pattern 1: High value transactions
        high_value = TransactionDetail.objects.filter(
            paid_amount__gte=100000,
            created_date__gte=timezone.now() - timedelta(days=7)
        )
        
        for txn in high_value[:10]:
            suspicious.append({
                'txn_id': txn.txn_id,
                'client_name': txn.client_name,
                'paid_amount': float(txn.paid_amount),
                'payment_mode': txn.payment_mode,
                'risk_score': txn.risk_score or 75,
                'created_date': txn.created_date,
                'risk_indicators': ['HIGH_VALUE']
            })
        
        return suspicious
    
    def calculate_compliance_score(self, kyc_summary, suspicious_count):
        """Calculate overall compliance score"""
        score = 0
        
        # KYC compliance (40 points)
        kyc_score = (kyc_summary['verified'] / kyc_summary['total_clients']) * 40 if kyc_summary['total_clients'] > 0 else 0
        score += kyc_score
        
        # Suspicious transactions (30 points)
        if suspicious_count > 10:
            score += 10
        elif suspicious_count > 5:
            score += 20
        else:
            score += 30
        
        # Pending reviews (15 points)
        pending = ComplianceAlert.objects.filter(status='OPEN').count()
        if pending == 0:
            score += 15
        elif pending < 5:
            score += 10
        elif pending < 10:
            score += 5
        
        # Audit completeness (15 points) - simplified
        score += 15
        
        return min(score, 100)
    
    @action(detail=False, methods=['post'])
    def generate_rbi_report(self, request):
        """Generate RBI compliance report"""
        report_type = request.data.get('report_type', 'DAILY')
        period_start = request.data.get('period_start', timezone.now().date() - timedelta(days=1))
        period_end = request.data.get('period_end', timezone.now().date())
        
        # Generate report data
        report_data = {
            'report_type': report_type,
            'period_start': str(period_start),
            'period_end': str(period_end),
            'generated_at': timezone.now().isoformat(),
            'organization': 'SabPaisa',
            'sections': {
                'transaction_summary': {
                    'total_transactions': 0,
                    'total_volume': 0,
                    'successful_transactions': 0,
                    'failed_transactions': 0
                },
                'kyc_compliance': {
                    'total_merchants': 0,
                    'kyc_completed': 0,
                    'kyc_pending': 0,
                    'compliance_rate': 0
                }
            }
        }
        
        # Create report file
        file_path = f"/tmp/rbi_report_{report_type}_{period_start}_{period_end}.json"
        with open(file_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        # Log report generation
        report_log = RBIReportLog.objects.create(
            report_type=report_type,
            report_period_start=period_start,
            report_period_end=period_end,
            generated_by=request.user.username,
            file_path=file_path,
            status='GENERATED'
        )
        
        return Response({
            'report_id': report_log.report_id,
            'file_path': file_path,
            'data': report_data
        })
    
    @action(detail=False, methods=['get'])
    def audit_trail(self, request):
        """Get audit trail logs"""
        logs = AdminUserActivityLog.objects.all().order_by('-timestamp')[:100]
        serializer = AuditLogSerializer(logs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def suspicious_transactions(self, request):
        """Get suspicious transactions with detailed analysis"""
        suspicious = self.detect_suspicious_transactions()
        return Response(suspicious)
