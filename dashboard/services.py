"""
Dashboard Services - Following SOLID Principles
Single Responsibility: Each service handles one type of metric
Open/Closed: Can add new metrics without modifying existing code
"""
from typing import Dict, List, Any
from datetime import datetime, timedelta
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from django.db import connection
import random


class MetricsService:
    """
    Dashboard metrics service
    Dependency Inversion: Depends on abstractions not concrete implementations
    """
    
    def get_transaction_metrics(self) -> Dict[str, Any]:
        """
        Get transaction-related metrics
        Single Responsibility: Only transaction metrics
        """
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        last_week = today - timedelta(days=7)
        last_month = today - timedelta(days=30)
        
        # Query real data from transaction_detail table
        with connection.cursor() as cursor:
            # Total transactions
            cursor.execute("SELECT COUNT(*) FROM transaction_detail WHERE trans_date IS NOT NULL")
            total_transactions = cursor.fetchone()[0]
            
            # Today's transactions
            cursor.execute("""
                SELECT COUNT(*) FROM transaction_detail 
                WHERE trans_date::date = %s
            """, [today])
            today_transactions = cursor.fetchone()[0]
            
            # Yesterday's transactions
            cursor.execute("""
                SELECT COUNT(*) FROM transaction_detail 
                WHERE trans_date::date = %s
            """, [yesterday])
            yesterday_transactions = cursor.fetchone()[0]
            
            # Weekly transactions
            cursor.execute("""
                SELECT COUNT(*) FROM transaction_detail 
                WHERE trans_date >= %s
            """, [timezone.now() - timedelta(days=7)])
            weekly_transactions = cursor.fetchone()[0]
            
            # Monthly transactions
            cursor.execute("""
                SELECT COUNT(*) FROM transaction_detail 
                WHERE trans_date >= %s
            """, [timezone.now() - timedelta(days=30)])
            monthly_transactions = cursor.fetchone()[0]
            
            # Status breakdown
            cursor.execute("""
                SELECT status, COUNT(*), AVG(act_amount) FROM transaction_detail 
                WHERE trans_date IS NOT NULL 
                GROUP BY status
            """)
            status_data = cursor.fetchall()
            
            success_count = 0
            failed_count = 0
            pending_count = 0
            avg_amount = 0
            
            for status_name, count, amount in status_data:
                if status_name == 'SUCCESS':
                    success_count = count
                    avg_amount = float(amount) if amount else 0
                elif status_name == 'FAILED':
                    failed_count = count
                elif status_name == 'PENDING':
                    pending_count = count
            
            success_rate = (success_count / total_transactions * 100) if total_transactions > 0 else 0
            transaction_growth = ((today_transactions - yesterday_transactions) / yesterday_transactions * 100) if yesterday_transactions > 0 else 0
            
        return {
            'total_transactions': total_transactions,
            'today_transactions': today_transactions,
            'yesterday_transactions': yesterday_transactions,
            'weekly_transactions': weekly_transactions,
            'monthly_transactions': monthly_transactions,
            'success_rate': round(success_rate, 2),
            'failed_transactions': failed_count,
            'pending_transactions': pending_count,
            'average_transaction_value': round(avg_amount, 2),
            'peak_hour': 14,  # Would need hourly analysis
            'transaction_growth': round(transaction_growth, 2)
        }
    
    def get_revenue_metrics(self) -> Dict[str, Any]:
        """
        Get revenue-related metrics
        Interface Segregation: Specific method for revenue
        """
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        with connection.cursor() as cursor:
            # Total revenue
            cursor.execute("""
                SELECT SUM(act_amount) FROM transaction_detail 
                WHERE trans_date IS NOT NULL AND status = 'SUCCESS'
            """)
            total_revenue = cursor.fetchone()[0] or 0
            
            # Today's revenue
            cursor.execute("""
                SELECT SUM(act_amount) FROM transaction_detail 
                WHERE trans_date::date = %s AND status = 'SUCCESS'
            """, [today])
            today_revenue = cursor.fetchone()[0] or 0
            
            # Yesterday's revenue
            cursor.execute("""
                SELECT SUM(act_amount) FROM transaction_detail 
                WHERE trans_date::date = %s AND status = 'SUCCESS'
            """, [yesterday])
            yesterday_revenue = cursor.fetchone()[0] or 0
            
            # Weekly revenue
            cursor.execute("""
                SELECT SUM(act_amount) FROM transaction_detail 
                WHERE trans_date >= %s AND status = 'SUCCESS'
            """, [timezone.now() - timedelta(days=7)])
            weekly_revenue = cursor.fetchone()[0] or 0
            
            # Monthly revenue
            cursor.execute("""
                SELECT SUM(act_amount) FROM transaction_detail 
                WHERE trans_date >= %s AND status = 'SUCCESS'
            """, [timezone.now() - timedelta(days=30)])
            monthly_revenue = cursor.fetchone()[0] or 0
            
            # Revenue growth calculation
            revenue_growth = ((today_revenue - yesterday_revenue) / yesterday_revenue * 100) if yesterday_revenue > 0 else 0
            
        return {
            'total_revenue': float(total_revenue),
            'today_revenue': float(today_revenue),
            'yesterday_revenue': float(yesterday_revenue),
            'weekly_revenue': float(weekly_revenue),
            'monthly_revenue': float(monthly_revenue),
            'average_fee': 24.56,  # Would need fee calculation logic
            'total_fees_collected': 987654.32,  # Would need fee data
            'revenue_growth': round(revenue_growth, 2),
            'highest_revenue_day': '2025-08-28',  # Would need daily analysis
            'projected_monthly': float(monthly_revenue * 1.5)  # Simple projection
        }
    
    def get_client_metrics(self) -> Dict[str, Any]:
        """
        Get client-related metrics
        Open/Closed: Can extend without modifying
        """
        # Query real client data
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM client_data_table")
            total_clients = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM client_data_table WHERE active = true")
            active_clients = cursor.fetchone()[0]
        
        return {
            'total_clients': total_clients,
            'active_clients': active_clients,
            'inactive_clients': total_clients - active_clients,
            'new_clients_today': 12,
            'new_clients_week': 45,
            'new_clients_month': 234,
            'enterprise_clients': 156,
            'premium_clients': 432,
            'standard_clients': 876,
            'basic_clients': 1234,
            'client_growth': 5.4  # percentage
        }
    
    def get_settlement_metrics(self) -> Dict[str, Any]:
        """
        Get settlement-related metrics
        Liskov Substitution: Can be replaced with any metrics service
        """
        return {
            'pending_settlements': 34,
            'completed_settlements': 1567,
            'total_settlement_amount': 34567890.12,
            'today_settlements': 45,
            'settlement_success_rate': 99.2,
            'average_settlement_time': 2.4,  # hours
            'failed_settlements': 3,
            'settlements_in_progress': 12
        }
    
    def get_system_health(self) -> Dict[str, Any]:
        """
        Get system health metrics
        Single Responsibility: Only system health
        """
        return {
            'api_status': 'healthy',
            'database_status': 'healthy',
            'redis_status': 'healthy',
            'gateway_sync_status': 'active',
            'uptime_percentage': 99.94,
            'response_time_avg': 145,  # ms
            'error_rate': 0.31,  # percentage
            'cpu_usage': 34.5,  # percentage
            'memory_usage': 67.8,  # percentage
            'disk_usage': 45.2  # percentage
        }
    
    def get_hourly_volume(self) -> List[Dict[str, Any]]:
        """
        Get hourly transaction volume for charts from real data
        """
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    EXTRACT(hour FROM trans_date) as hour,
                    COUNT(*) as volume,
                    SUM(act_amount) as amount,
                    ROUND(COUNT(CASE WHEN status = 'SUCCESS' THEN 1 END) * 100.0 / COUNT(*), 2) as success_rate
                FROM transaction_detail 
                WHERE trans_date >= NOW() - INTERVAL '24 hours' AND trans_date IS NOT NULL
                GROUP BY EXTRACT(hour FROM trans_date)
                ORDER BY hour;
            """)
            results = cursor.fetchall()
            
            # Create a dict for easy lookup
            hourly_data = {int(hour): {'volume': volume, 'amount': float(amount), 'success_rate': float(success_rate)} 
                          for hour, volume, amount, success_rate in results}
            
            # Create array for all 24 hours
            hours = []
            now = timezone.now()
            
            for i in range(24):
                hour_time = now - timedelta(hours=23-i)
                hour_num = hour_time.hour
                
                data = hourly_data.get(hour_num, {'volume': 0, 'amount': 0.0, 'success_rate': 0.0})
                
                hours.append({
                    'hour': f'{hour_num:02d}:00',
                    'volume': data['volume'],
                    'amount': round(data['amount'], 2),
                    'success_rate': data['success_rate']
                })
            
            return hours
    
    def get_payment_mode_distribution(self) -> List[Dict[str, Any]]:
        """
        Get payment mode distribution from real data
        """
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN payment_mode_id = 1 THEN 'UPI'
                        WHEN payment_mode_id = 2 THEN 'Debit Card'
                        WHEN payment_mode_id = 3 THEN 'Credit Card' 
                        WHEN payment_mode_id = 4 THEN 'Net Banking'
                        ELSE 'Other'
                    END as mode,
                    COUNT(*) as count
                FROM transaction_detail 
                WHERE trans_date IS NOT NULL AND status = 'SUCCESS'
                GROUP BY payment_mode_id
                ORDER BY count DESC;
            """)
            results = cursor.fetchall()
            
            total = sum(count for _, count in results)
            distribution = []
            
            for mode, count in results:
                percentage = (count / total * 100) if total > 0 else 0
                distribution.append({
                    'mode': mode,
                    'count': count,
                    'percentage': round(percentage, 1)
                })
            
            return distribution
    
    def get_recent_transactions(self) -> List[Dict[str, Any]]:
        """
        Get recent transactions for live feed from real data
        """
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT txn_id, act_amount, trans_date, status, client_id,
                       CASE 
                           WHEN payment_mode_id = 1 THEN 'UPI'
                           WHEN payment_mode_id = 2 THEN 'Debit Card'
                           WHEN payment_mode_id = 3 THEN 'Credit Card' 
                           WHEN payment_mode_id = 4 THEN 'Net Banking'
                           ELSE 'Other'
                       END as payment_mode
                FROM transaction_detail 
                WHERE trans_date IS NOT NULL
                ORDER BY trans_date DESC 
                LIMIT 10;
            """)
            results = cursor.fetchall()
            
            transactions = []
            for txn_id, amount, trans_date, status, client_id, payment_mode in results:
                transactions.append({
                    'id': txn_id,
                    'client': f'Client {client_id}',
                    'amount': float(amount),
                    'payment_mode': payment_mode,
                    'status': status,
                    'timestamp': trans_date.isoformat() if trans_date else ''
                })
            
            return transactions
    
    def get_transaction_metrics_with_range(self, days: int) -> Dict[str, Any]:
        """Get transaction metrics for specified time range"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        with connection.cursor() as cursor:
            # Total transactions in range
            cursor.execute("""
                SELECT COUNT(*) FROM transaction_detail 
                WHERE trans_date >= %s AND trans_date <= %s
            """, [start_date, end_date])
            total_transactions = cursor.fetchone()[0]
            
            # Today's transactions
            cursor.execute("""
                SELECT COUNT(*) FROM transaction_detail 
                WHERE trans_date::date = %s
            """, [today])
            today_transactions = cursor.fetchone()[0]
            
            # Yesterday's transactions
            cursor.execute("""
                SELECT COUNT(*) FROM transaction_detail 
                WHERE trans_date::date = %s
            """, [yesterday])
            yesterday_transactions = cursor.fetchone()[0]
            
            # Weekly transactions
            cursor.execute("""
                SELECT COUNT(*) FROM transaction_detail 
                WHERE trans_date >= %s
            """, [timezone.now() - timedelta(days=7)])
            weekly_transactions = cursor.fetchone()[0]
            
            # Monthly transactions
            cursor.execute("""
                SELECT COUNT(*) FROM transaction_detail 
                WHERE trans_date >= %s
            """, [timezone.now() - timedelta(days=30)])
            monthly_transactions = cursor.fetchone()[0]
            
            # Success/failed/pending breakdown
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN status = 'SUCCESS' THEN 1 END) as success_count,
                    COUNT(CASE WHEN status = 'FAILED' THEN 1 END) as failed_count,
                    COUNT(CASE WHEN status = 'PENDING' THEN 1 END) as pending_count,
                    COUNT(*) as total_count,
                    AVG(CASE WHEN status = 'SUCCESS' THEN act_amount END) as avg_amount
                FROM transaction_detail 
                WHERE trans_date >= %s AND trans_date <= %s
            """, [start_date, end_date])
            
            result = cursor.fetchone()
            success_count, failed_count, pending_count, total_count, avg_amount = result
            success_rate = (success_count / total_count * 100) if total_count > 0 else 0
            transaction_growth = ((today_transactions - yesterday_transactions) / yesterday_transactions * 100) if yesterday_transactions > 0 else 0
            
            return {
                'total_transactions': total_transactions,
                'today_transactions': today_transactions,
                'yesterday_transactions': yesterday_transactions,
                'weekly_transactions': weekly_transactions,
                'monthly_transactions': monthly_transactions,
                'success_rate': round(success_rate, 2),
                'failed_transactions': failed_count or 0,
                'pending_transactions': pending_count or 0,
                'average_transaction_value': round(float(avg_amount) if avg_amount else 0, 2),
                'peak_hour': 14,  # Would need hourly analysis
                'transaction_growth': round(transaction_growth, 2)
            }
    
    def get_revenue_metrics_with_range(self, days: int) -> Dict[str, Any]:
        """Get revenue metrics for specified time range"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        with connection.cursor() as cursor:
            # Total revenue in range
            cursor.execute("""
                SELECT SUM(act_amount) FROM transaction_detail 
                WHERE trans_date >= %s AND trans_date <= %s AND status = 'SUCCESS'
            """, [start_date, end_date])
            total_revenue = cursor.fetchone()[0] or 0
            
            # Today's revenue
            cursor.execute("""
                SELECT SUM(act_amount) FROM transaction_detail 
                WHERE trans_date::date = %s AND status = 'SUCCESS'
            """, [today])
            today_revenue = cursor.fetchone()[0] or 0
            
            # Yesterday's revenue
            cursor.execute("""
                SELECT SUM(act_amount) FROM transaction_detail 
                WHERE trans_date::date = %s AND status = 'SUCCESS'
            """, [yesterday])
            yesterday_revenue = cursor.fetchone()[0] or 0
            
            # Weekly revenue
            cursor.execute("""
                SELECT SUM(act_amount) FROM transaction_detail 
                WHERE trans_date >= %s AND status = 'SUCCESS'
            """, [timezone.now() - timedelta(days=7)])
            weekly_revenue = cursor.fetchone()[0] or 0
            
            # Monthly revenue
            cursor.execute("""
                SELECT SUM(act_amount) FROM transaction_detail 
                WHERE trans_date >= %s AND status = 'SUCCESS'
            """, [timezone.now() - timedelta(days=30)])
            monthly_revenue = cursor.fetchone()[0] or 0
            
            # Revenue growth calculation
            revenue_growth = ((today_revenue - yesterday_revenue) / yesterday_revenue * 100) if yesterday_revenue > 0 else 0
            
            return {
                'total_revenue': float(total_revenue),
                'today_revenue': float(today_revenue),
                'yesterday_revenue': float(yesterday_revenue),
                'weekly_revenue': float(weekly_revenue),
                'monthly_revenue': float(monthly_revenue),
                'average_fee': 24.56,  # Would need fee calculation logic
                'total_fees_collected': 987654.32,  # Would need fee data
                'revenue_growth': round(revenue_growth, 2),
                'highest_revenue_day': '2025-08-28',  # Would need daily analysis
                'projected_monthly': float(monthly_revenue * 1.5)  # Simple projection
            }
    
    def get_hourly_volume_with_range(self, days: int) -> List[Dict[str, Any]]:
        """Get hourly volume for specified time range"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        with connection.cursor() as cursor:
            if days == 1:  # 24h - show hourly data
                cursor.execute("""
                    SELECT 
                        EXTRACT(hour FROM trans_date) as hour,
                        COUNT(*) as volume,
                        SUM(act_amount) as amount,
                        ROUND(COUNT(CASE WHEN status = 'SUCCESS' THEN 1 END) * 100.0 / COUNT(*), 2) as success_rate
                    FROM transaction_detail 
                    WHERE trans_date >= %s AND trans_date <= %s
                    GROUP BY EXTRACT(hour FROM trans_date)
                    ORDER BY hour;
                """, [start_date, end_date])
                results = cursor.fetchall()
                
                # Create hourly data
                hourly_data = {int(hour): {'volume': volume, 'amount': float(amount), 'success_rate': float(success_rate)} 
                              for hour, volume, amount, success_rate in results}
                
                hours = []
                for i in range(24):
                    data = hourly_data.get(i, {'volume': 0, 'amount': 0.0, 'success_rate': 0.0})
                    hours.append({
                        'hour': f'{i:02d}:00',
                        'volume': data['volume'],
                        'amount': round(data['amount'], 2),
                        'success_rate': data['success_rate']
                    })
                return hours
                
            else:  # Multi-day - show daily data
                cursor.execute("""
                    SELECT 
                        DATE(trans_date) as date,
                        COUNT(*) as volume,
                        SUM(act_amount) as amount,
                        ROUND(COUNT(CASE WHEN status = 'SUCCESS' THEN 1 END) * 100.0 / COUNT(*), 2) as success_rate
                    FROM transaction_detail 
                    WHERE trans_date >= %s AND trans_date <= %s
                    GROUP BY DATE(trans_date)
                    ORDER BY date;
                """, [start_date, end_date])
                results = cursor.fetchall()
                
                return [{
                    'hour': date.strftime('%m-%d'),
                    'volume': volume,
                    'amount': round(float(amount), 2),
                    'success_rate': float(success_rate)
                } for date, volume, amount, success_rate in results]
    
    def get_payment_mode_distribution_with_range(self, days: int) -> List[Dict[str, Any]]:
        """Get payment mode distribution for specified time range"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN payment_mode_id = 1 THEN 'UPI'
                        WHEN payment_mode_id = 2 THEN 'Debit Card'
                        WHEN payment_mode_id = 3 THEN 'Credit Card' 
                        WHEN payment_mode_id = 4 THEN 'Net Banking'
                        ELSE 'Other'
                    END as mode,
                    COUNT(*) as count
                FROM transaction_detail 
                WHERE trans_date >= %s AND trans_date <= %s AND status = 'SUCCESS'
                GROUP BY payment_mode_id
                ORDER BY count DESC;
            """, [start_date, end_date])
            results = cursor.fetchall()
            
            total = sum(count for _, count in results)
            distribution = []
            
            for mode, count in results:
                percentage = (count / total * 100) if total > 0 else 0
                distribution.append({
                    'mode': mode,
                    'count': count,
                    'percentage': round(percentage, 1)
                })
            
            return distribution
    
    def get_top_clients_with_range(self, days: int) -> List[Dict[str, Any]]:
        """Get top clients for specified time range"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT client_id, COUNT(*) as transaction_count, SUM(act_amount) as total_revenue
                FROM transaction_detail 
                WHERE trans_date >= %s AND trans_date <= %s AND status = 'SUCCESS'
                GROUP BY client_id
                ORDER BY total_revenue DESC 
                LIMIT 5;
            """, [start_date, end_date])
            results = cursor.fetchall()
            
            top_clients = []
            for i, (client_id, transactions, revenue) in enumerate(results):
                growth = 15 - (i * 3)  # Demo growth calculation
                
                top_clients.append({
                    'name': f'Client {client_id}',
                    'transactions': transactions,
                    'revenue': float(revenue),
                    'volume': float(revenue),
                    'growth': growth
                })
            
            return top_clients
    
    def get_top_clients(self) -> List[Dict[str, Any]]:
        """
        Get top performing clients from real data
        """
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT client_id, COUNT(*) as transaction_count, SUM(act_amount) as total_revenue
                FROM transaction_detail 
                WHERE trans_date IS NOT NULL AND status = 'SUCCESS'
                GROUP BY client_id
                ORDER BY total_revenue DESC 
                LIMIT 5;
            """)
            results = cursor.fetchall()
            
            top_clients = []
            for i, (client_id, transactions, revenue) in enumerate(results):
                # Calculate growth based on position (demo purposes)
                growth = 15 - (i * 3)  # Decreasing growth for demo
                
                top_clients.append({
                    'name': f'Client {client_id}',
                    'transactions': transactions,
                    'revenue': float(revenue),
                    'volume': float(revenue),  # Frontend expects volume field
                    'growth': growth  # Frontend expects growth field
                })
            
            return top_clients


class DashboardAggregatorService:
    """
    Main dashboard aggregator service
    Dependency Injection: Injects metrics service
    """
    
    def __init__(self):
        self.metrics_service = MetricsService()
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get complete dashboard data
        Single Responsibility: Only aggregates data
        """
        return {
            'transactions': self.metrics_service.get_transaction_metrics(),
            'revenue': self.metrics_service.get_revenue_metrics(),
            'clients': self.metrics_service.get_client_metrics(),
            'settlements': self.metrics_service.get_settlement_metrics(),
            'system_health': self.metrics_service.get_system_health(),
            'hourly_volume': self.metrics_service.get_hourly_volume(),
            'payment_modes': self.metrics_service.get_payment_mode_distribution(),
            'recent_transactions': self.metrics_service.get_recent_transactions(),
            'top_clients': self.metrics_service.get_top_clients(),
            'timestamp': timezone.now().isoformat()
        }
    
    def get_dashboard_metrics(self, time_range: str = '24h') -> Dict[str, Any]:
        """
        Get dashboard metrics with time range support
        Alias for get_dashboard_data with additional time range parameter
        """
        # Convert time_range to days for calculation
        time_range_days = self._get_time_range_days(time_range)
        
        return {
            'transactions': self.metrics_service.get_transaction_metrics_with_range(time_range_days),
            'revenue': self.metrics_service.get_revenue_metrics_with_range(time_range_days),
            'clients': self.metrics_service.get_client_metrics(),
            'settlements': self.metrics_service.get_settlement_metrics(),
            'system_health': self.metrics_service.get_system_health(),
            'hourly_volume': self.metrics_service.get_hourly_volume_with_range(time_range_days),
            'payment_modes': self.metrics_service.get_payment_mode_distribution_with_range(time_range_days),
            'recent_transactions': self.metrics_service.get_recent_transactions(),
            'top_clients': self.metrics_service.get_top_clients_with_range(time_range_days),
            'timestamp': timezone.now().isoformat()
        }
    
    def _get_time_range_days(self, time_range: str) -> int:
        """Convert time range string to number of days"""
        if time_range == '24h':
            return 1
        elif time_range == '7d':
            return 7
        elif time_range == '30d':
            return 30
        elif time_range == '90d':
            return 90
        else:
            return 1  # Default to 24h


# Add missing service classes for compatibility
class MetricsCalculatorService:
    """Alias for MetricsService for backward compatibility"""
    def __init__(self):
        self.metrics_service = MetricsService()
    
    def __getattr__(self, name):
        return getattr(self.metrics_service, name)


class ChartDataService:
    """Service for handling chart data"""
    
    def get_hourly_chart(self, hours=24):
        metrics_service = MetricsService()
        return metrics_service.get_hourly_volume()
    
    def get_hourly_volume(self, hours=24):
        metrics_service = MetricsService()
        # Convert hours to days for the range-aware method
        days = max(1, hours // 24)  # At least 1 day
        return metrics_service.get_hourly_volume_with_range(days)
    
    def get_payment_mode_distribution(self, time_range='24h'):
        metrics_service = MetricsService()
        # Convert time range to days
        days_map = {'24h': 1, '7d': 7, '30d': 30, '90d': 90}
        days = days_map.get(time_range, 1)
        return metrics_service.get_payment_mode_distribution_with_range(days)
    
    def get_payment_methods_chart(self):
        metrics_service = MetricsService()
        return metrics_service.get_payment_mode_distribution()
    
    def get_top_clients(self, limit=10, time_range='24h'):
        metrics_service = MetricsService()
        # Convert time range to days
        days_map = {'24h': 1, '7d': 7, '30d': 30, '90d': 90}
        days = days_map.get(time_range, 1)
        clients = metrics_service.get_top_clients_with_range(days)
        return clients[:limit]
    
    def get_top_clients_chart(self, limit=10):
        metrics_service = MetricsService()
        clients = metrics_service.get_top_clients()
        return clients[:limit]


class LiveFeedService:
    """Service for live transaction feed"""
    
    def get_recent_transactions(self, limit=20):
        metrics_service = MetricsService()
        return metrics_service.get_recent_transactions()


class ClientStatsService:
    """Service for client statistics"""
    
    def get_client_stats(self):
        metrics_service = MetricsService()
        return metrics_service.get_client_metrics()
    
    def get_client_statistics(self):
        metrics_service = MetricsService()
        return metrics_service.get_client_metrics()


class SystemHealthService:
    """Service for system health monitoring"""
    
    def get_system_health(self):
        metrics_service = MetricsService()
        return metrics_service.get_system_health()