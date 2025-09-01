"""
Email Notification Service
Handles all email notifications across the system
"""
import logging
from typing import List, Dict, Any, Optional
from django.core.mail import send_mail, send_mass_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from celery import shared_task
import os

logger = logging.getLogger(__name__)


class EmailNotificationService:
    """
    Service for sending email notifications
    """
    
    def __init__(self):
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@sabpaisa.com')
        self.admin_emails = getattr(settings, 'ADMIN_EMAILS', [])
        
    def send_transaction_notification(self, transaction_data: Dict[str, Any]) -> bool:
        """
        Send transaction notification email
        """
        try:
            subject = f"Transaction {transaction_data['status']} - {transaction_data['transaction_id']}"
            
            context = {
                'transaction': transaction_data,
                'timestamp': timezone.now(),
                'support_email': 'support@sabpaisa.com'
            }
            
            # Render HTML template
            html_content = render_to_string('emails/transaction_notification.html', context)
            text_content = self._generate_text_content('transaction', context)
            
            # Send email
            return self._send_email(
                subject=subject,
                recipients=[transaction_data['email']],
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error(f"Failed to send transaction notification: {str(e)}")
            return False
    
    def send_settlement_notification(self, settlement_data: Dict[str, Any]) -> bool:
        """
        Send settlement notification email
        """
        try:
            subject = f"Settlement Processed - Batch {settlement_data['batch_id']}"
            
            context = {
                'settlement': settlement_data,
                'timestamp': timezone.now(),
                'portal_url': 'https://admin.sabpaisa.com/settlements'
            }
            
            html_content = render_to_string('emails/settlement_notification.html', context)
            text_content = self._generate_text_content('settlement', context)
            
            recipients = settlement_data.get('recipients', self.admin_emails)
            
            return self._send_email(
                subject=subject,
                recipients=recipients,
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error(f"Failed to send settlement notification: {str(e)}")
            return False
    
    def send_refund_notification(self, refund_data: Dict[str, Any]) -> bool:
        """
        Send refund notification email
        """
        try:
            subject = f"Refund {refund_data['status']} - {refund_data['refund_id']}"
            
            context = {
                'refund': refund_data,
                'timestamp': timezone.now(),
                'expected_date': refund_data.get('expected_date', 'within 5-7 business days')
            }
            
            html_content = render_to_string('emails/refund_notification.html', context)
            text_content = self._generate_text_content('refund', context)
            
            return self._send_email(
                subject=subject,
                recipients=[refund_data['email']],
                html_content=html_content,
                text_content=text_content,
                cc=self.admin_emails
            )
            
        except Exception as e:
            logger.error(f"Failed to send refund notification: {str(e)}")
            return False
    
    def send_mfa_setup_notification(self, user_data: Dict[str, Any]) -> bool:
        """
        Send MFA setup notification
        """
        try:
            subject = "Multi-Factor Authentication Enabled"
            
            context = {
                'user': user_data,
                'timestamp': timezone.now(),
                'security_url': 'https://admin.sabpaisa.com/security'
            }
            
            html_content = render_to_string('emails/mfa_setup.html', context)
            text_content = self._generate_text_content('mfa_setup', context)
            
            return self._send_email(
                subject=subject,
                recipients=[user_data['email']],
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error(f"Failed to send MFA setup notification: {str(e)}")
            return False
    
    def send_alert_notification(self, alert_data: Dict[str, Any]) -> bool:
        """
        Send system alert notification
        """
        try:
            subject = f"[{alert_data['severity']}] System Alert: {alert_data['title']}"
            
            context = {
                'alert': alert_data,
                'timestamp': timezone.now(),
                'dashboard_url': 'https://admin.sabpaisa.com/dashboard'
            }
            
            html_content = render_to_string('emails/system_alert.html', context)
            text_content = self._generate_text_content('alert', context)
            
            recipients = alert_data.get('recipients', self.admin_emails)
            
            return self._send_email(
                subject=subject,
                recipients=recipients,
                html_content=html_content,
                text_content=text_content,
                priority='high' if alert_data['severity'] == 'CRITICAL' else 'normal'
            )
            
        except Exception as e:
            logger.error(f"Failed to send alert notification: {str(e)}")
            return False
    
    def send_bulk_notification(self, notification_type: str, recipients_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Send bulk notifications
        """
        success_count = 0
        failed_count = 0
        errors = []
        
        for recipient in recipients_data:
            try:
                if notification_type == 'transaction':
                    success = self.send_transaction_notification(recipient)
                elif notification_type == 'settlement':
                    success = self.send_settlement_notification(recipient)
                elif notification_type == 'refund':
                    success = self.send_refund_notification(recipient)
                else:
                    success = False
                
                if success:
                    success_count += 1
                else:
                    failed_count += 1
                    errors.append(recipient.get('email', 'unknown'))
                    
            except Exception as e:
                failed_count += 1
                errors.append(f"{recipient.get('email', 'unknown')}: {str(e)}")
        
        return {
            'success_count': success_count,
            'failed_count': failed_count,
            'errors': errors[:10]  # Return first 10 errors
        }
    
    def send_daily_summary(self) -> bool:
        """
        Send daily summary email to admins
        """
        try:
            from dashboard.services import DashboardAggregatorService
            from transactions.services import TransactionAnalyticsService
            from settlements.services import SettlementAnalyticsService
            
            # Get analytics data
            dashboard_service = DashboardAggregatorService()
            transaction_service = TransactionAnalyticsService()
            settlement_service = SettlementAnalyticsService()
            
            metrics = dashboard_service.get_dashboard_metrics('24h')
            transaction_stats = transaction_service.get_daily_statistics()
            settlement_stats = settlement_service.get_daily_statistics()
            
            context = {
                'date': timezone.now().date(),
                'metrics': metrics,
                'transaction_stats': transaction_stats,
                'settlement_stats': settlement_stats,
                'dashboard_url': 'https://admin.sabpaisa.com/dashboard'
            }
            
            subject = f"Daily Summary - {context['date']}"
            html_content = render_to_string('emails/daily_summary.html', context)
            text_content = self._generate_text_content('daily_summary', context)
            
            return self._send_email(
                subject=subject,
                recipients=self.admin_emails,
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error(f"Failed to send daily summary: {str(e)}")
            return False
    
    def send_client_onboarding_notification(self, client_data: Dict[str, Any]) -> bool:
        """
        Send client onboarding notification
        """
        try:
            subject = f"Welcome to SabPaisa - {client_data['client_name']}"
            
            context = {
                'client': client_data,
                'timestamp': timezone.now(),
                'portal_url': 'https://admin.sabpaisa.com',
                'documentation_url': 'https://docs.sabpaisa.com',
                'support_email': 'support@sabpaisa.com'
            }
            
            html_content = render_to_string('emails/client_onboarding.html', context)
            text_content = self._generate_text_content('onboarding', context)
            
            return self._send_email(
                subject=subject,
                recipients=[client_data['email']],
                html_content=html_content,
                text_content=text_content,
                attachments=self._get_onboarding_attachments()
            )
            
        except Exception as e:
            logger.error(f"Failed to send onboarding notification: {str(e)}")
            return False
    
    def send_payment_configuration_update(self, config_data: Dict[str, Any]) -> bool:
        """
        Send payment configuration update notification
        """
        try:
            subject = f"Payment Configuration Updated - {config_data['client_name']}"
            
            context = {
                'config': config_data,
                'timestamp': timezone.now(),
                'changes': config_data.get('changes', []),
                'effective_date': config_data.get('effective_date', 'immediately')
            }
            
            html_content = render_to_string('emails/config_update.html', context)
            text_content = self._generate_text_content('config_update', context)
            
            recipients = [config_data['email']] + self.admin_emails
            
            return self._send_email(
                subject=subject,
                recipients=recipients,
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error(f"Failed to send configuration update: {str(e)}")
            return False
    
    # Helper methods
    def _send_email(self, subject: str, recipients: List[str], 
                   html_content: str, text_content: str,
                   cc: List[str] = None, bcc: List[str] = None,
                   attachments: List[tuple] = None, priority: str = 'normal') -> bool:
        """
        Send email with HTML and text content
        """
        try:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=self.from_email,
                to=recipients,
                cc=cc or [],
                bcc=bcc or []
            )
            
            msg.attach_alternative(html_content, "text/html")
            
            # Add priority header
            if priority == 'high':
                msg.extra_headers = {'X-Priority': '1', 'Importance': 'high'}
            
            # Add attachments
            if attachments:
                for filename, content, mimetype in attachments:
                    msg.attach(filename, content, mimetype)
            
            msg.send()
            
            logger.info(f"Email sent successfully: {subject} to {recipients}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    def _generate_text_content(self, template_type: str, context: Dict[str, Any]) -> str:
        """
        Generate plain text content from context
        """
        # Basic text templates
        templates = {
            'transaction': """
Transaction {transaction[status]}
ID: {transaction[transaction_id]}
Amount: {transaction[amount]}
Date: {timestamp}

For support, contact: {support_email}
            """,
            'settlement': """
Settlement Processed
Batch ID: {settlement[batch_id]}
Amount: {settlement[amount]}
Date: {timestamp}

View details: {portal_url}
            """,
            'refund': """
Refund {refund[status]}
ID: {refund[refund_id]}
Amount: {refund[amount]}
Expected: {expected_date}

Date: {timestamp}
            """,
            'alert': """
System Alert: {alert[title]}
Severity: {alert[severity]}
Message: {alert[message]}
Date: {timestamp}

Dashboard: {dashboard_url}
            """,
            'daily_summary': """
Daily Summary for {date}

Transactions: {metrics[total_transactions]}
Total Volume: {metrics[total_volume]}
Settlements: {settlement_stats[count]}
Success Rate: {transaction_stats[success_rate]}%

View full report: {dashboard_url}
            """
        }
        
        template = templates.get(template_type, "Notification from SabPaisa Admin")
        
        try:
            return template.format(**context)
        except:
            return f"Notification: {template_type}"
    
    def _get_onboarding_attachments(self) -> List[tuple]:
        """
        Get onboarding documentation attachments
        """
        attachments = []
        
        # Add API documentation if exists
        doc_path = os.path.join(settings.MEDIA_ROOT, 'docs', 'api_documentation.pdf')
        if os.path.exists(doc_path):
            with open(doc_path, 'rb') as f:
                attachments.append(('API_Documentation.pdf', f.read(), 'application/pdf'))
        
        return attachments


# Celery tasks for async email sending
@shared_task
def send_email_async(email_type: str, data: Dict[str, Any]):
    """
    Async task to send email notifications
    """
    service = EmailNotificationService()
    
    if email_type == 'transaction':
        return service.send_transaction_notification(data)
    elif email_type == 'settlement':
        return service.send_settlement_notification(data)
    elif email_type == 'refund':
        return service.send_refund_notification(data)
    elif email_type == 'mfa_setup':
        return service.send_mfa_setup_notification(data)
    elif email_type == 'alert':
        return service.send_alert_notification(data)
    elif email_type == 'onboarding':
        return service.send_client_onboarding_notification(data)
    elif email_type == 'config_update':
        return service.send_payment_configuration_update(data)
    else:
        logger.error(f"Unknown email type: {email_type}")
        return False


@shared_task
def send_daily_summary_task():
    """
    Scheduled task to send daily summary
    """
    service = EmailNotificationService()
    return service.send_daily_summary()