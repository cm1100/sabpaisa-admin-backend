import hashlib
import hmac
import json
import logging
import time
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views import View
from typing import Dict, Any, Optional

from .models import GatewayWebhookLog, GatewayConfiguration, TransactionDetail, GatewaySyncQueue
from .tasks import queue_status_check, queue_refund_status_check

logger = logging.getLogger('apps')


class WebhookSignatureVerifier:
    """Utility class for webhook signature verification"""
    
    @staticmethod
    def verify_signature(payload: bytes, signature: str, secret: str, algorithm: str = 'sha256') -> bool:
        """Verify webhook signature"""
        try:
            if algorithm == 'sha256':
                expected_signature = hmac.new(
                    secret.encode('utf-8'),
                    payload,
                    hashlib.sha256
                ).hexdigest()
                
                # Handle different signature formats
                if signature.startswith('sha256='):
                    signature = signature[7:]
                
                return hmac.compare_digest(expected_signature, signature)
            
            return False
        except Exception as e:
            logger.error(f"Signature verification error: {str(e)}")
            return False


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(require_POST, name='dispatch')
class GatewayWebhookView(View):
    """Handle webhook calls from payment gateways"""
    
    def post(self, request, gateway_code):
        start_time = time.time()
        
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR', '127.0.0.1')
        
        # Get request headers and body
        headers = dict(request.headers)
        try:
            body_data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            body_data = {'raw_body': request.body.decode('utf-8', errors='ignore')}
        
        # Initialize log entry
        webhook_log = GatewayWebhookLog.objects.create(
            gateway_code=gateway_code,
            webhook_type='UNKNOWN',
            request_headers=headers,
            request_body=body_data,
            response_status=200,  # Default, will be updated
            ip_address=ip_address,
            signature_valid=False,
            processed=False
        )
        
        try:
            # Get gateway configuration
            try:
                gateway_config = GatewayConfiguration.objects.get(
                    gateway_code=gateway_code,
                    is_active=True
                )
            except GatewayConfiguration.DoesNotExist:
                webhook_log.response_status = 404
                webhook_log.response_body = {'error': f'Gateway {gateway_code} not found or inactive'}
                webhook_log.save()
                return JsonResponse({'error': 'Gateway not found'}, status=404)
            
            # Verify signature if webhook secret is configured
            signature_valid = True
            if gateway_config.webhook_secret:
                signature = headers.get('X-Signature') or headers.get('Authorization') or headers.get('Signature')
                if signature:
                    signature_valid = WebhookSignatureVerifier.verify_signature(
                        request.body,
                        signature,
                        gateway_config.webhook_secret
                    )
                else:
                    signature_valid = False
            
            webhook_log.signature_valid = signature_valid
            
            # Process webhook data
            webhook_type = self._determine_webhook_type(body_data)
            webhook_log.webhook_type = webhook_type
            
            # Extract transaction IDs
            txn_id = body_data.get('txn_id') or body_data.get('transaction_id') or body_data.get('order_id')
            pg_txn_id = body_data.get('pg_txn_id') or body_data.get('gateway_txn_id') or body_data.get('reference_id')
            
            webhook_log.txn_id = txn_id
            webhook_log.pg_txn_id = pg_txn_id
            
            if not signature_valid:
                webhook_log.response_status = 401
                webhook_log.response_body = {'error': 'Invalid signature'}
                webhook_log.save()
                return JsonResponse({'error': 'Invalid signature'}, status=401)
            
            # Process based on webhook type
            response_data = {}
            if webhook_type == 'PAYMENT_STATUS':
                response_data = self._process_payment_status(body_data, txn_id, pg_txn_id)
            elif webhook_type == 'REFUND_STATUS':
                response_data = self._process_refund_status(body_data, txn_id, pg_txn_id)
            elif webhook_type == 'SETTLEMENT':
                response_data = self._process_settlement_status(body_data, txn_id, pg_txn_id)
            else:
                response_data = {'status': 'received', 'message': 'Webhook processed but type unknown'}
            
            # Update log with processing results
            processing_time = (time.time() - start_time) * 1000
            webhook_log.processing_time_ms = int(processing_time)
            webhook_log.processed = True
            webhook_log.response_body = response_data
            webhook_log.save()
            
            logger.info(f"Webhook processed: {gateway_code} - {webhook_type} in {processing_time:.2f}ms")
            return JsonResponse(response_data)
            
        except Exception as e:
            # Log error
            error_msg = str(e)
            processing_time = (time.time() - start_time) * 1000
            webhook_log.processing_time_ms = int(processing_time)
            webhook_log.response_status = 500
            webhook_log.response_body = {'error': error_msg}
            webhook_log.save()
            
            logger.error(f"Webhook processing error for {gateway_code}: {error_msg}")
            return JsonResponse({'error': 'Internal server error'}, status=500)
    
    def _determine_webhook_type(self, data: Dict[str, Any]) -> str:
        """Determine webhook type from payload"""
        # Common webhook type indicators
        if 'payment_status' in data or 'transaction_status' in data:
            return 'PAYMENT_STATUS'
        elif 'refund_status' in data or 'refund_id' in data:
            return 'REFUND_STATUS'
        elif 'settlement' in data or 'settlement_status' in data:
            return 'SETTLEMENT'
        elif 'event_type' in data:
            event_type = data['event_type'].upper()
            if 'PAYMENT' in event_type:
                return 'PAYMENT_STATUS'
            elif 'REFUND' in event_type:
                return 'REFUND_STATUS'
            elif 'SETTLEMENT' in event_type:
                return 'SETTLEMENT'
        
        return 'UNKNOWN'
    
    def _process_payment_status(self, data: Dict[str, Any], txn_id: str, pg_txn_id: str) -> Dict[str, Any]:
        """Process payment status webhook"""
        try:
            if not txn_id:
                return {'error': 'Transaction ID missing in webhook'}
            
            # Update transaction if it exists
            try:
                transaction = TransactionDetail.objects.get(txn_id=txn_id)
                
                # Update status if provided
                new_status = data.get('status') or data.get('payment_status') or data.get('transaction_status')
                if new_status:
                    transaction.status = new_status.upper()
                
                # Update other fields
                if 'pg_response_code' in data:
                    transaction.pg_response_code = data['pg_response_code']
                if 'response_message' in data:
                    transaction.resp_msg = data['response_message']
                
                transaction.save()
                
                # Queue immediate status check for verification
                queue_status_check.delay(txn_id, pg_txn_id, priority=1)
                
                return {
                    'status': 'success',
                    'message': 'Payment status updated',
                    'txn_id': txn_id,
                    'updated_status': transaction.status
                }
                
            except TransactionDetail.DoesNotExist:
                # Transaction not found, queue for later processing
                logger.warning(f"Transaction {txn_id} not found, queuing for later sync")
                queue_status_check.delay(txn_id, pg_txn_id, priority=2)
                
                return {
                    'status': 'queued',
                    'message': 'Transaction not found, queued for sync',
                    'txn_id': txn_id
                }
                
        except Exception as e:
            logger.error(f"Error processing payment status webhook: {str(e)}")
            return {'error': f'Payment status processing failed: {str(e)}'}
    
    def _process_refund_status(self, data: Dict[str, Any], txn_id: str, pg_txn_id: str) -> Dict[str, Any]:
        """Process refund status webhook"""
        try:
            if not txn_id:
                return {'error': 'Transaction ID missing in webhook'}
            
            # Update transaction refund details
            try:
                transaction = TransactionDetail.objects.get(txn_id=txn_id)
                
                # Update refund fields
                if 'refund_status' in data:
                    transaction.refund_status_code = data['refund_status']
                if 'is_refunded' in data:
                    transaction.is_refunded = data['is_refunded']
                if 'refunded_amount' in data:
                    transaction.refunded_amount = float(data['refunded_amount'])
                if 'refund_message' in data:
                    transaction.refund_message = data['refund_message']
                if 'refunded_date' in data:
                    transaction.refunded_date = timezone.datetime.fromisoformat(data['refunded_date'])
                
                transaction.save()
                
                # Queue refund status verification
                queue_refund_status_check.delay(txn_id, pg_txn_id, priority=1)
                
                return {
                    'status': 'success',
                    'message': 'Refund status updated',
                    'txn_id': txn_id,
                    'is_refunded': transaction.is_refunded
                }
                
            except TransactionDetail.DoesNotExist:
                logger.warning(f"Transaction {txn_id} not found for refund webhook")
                queue_refund_status_check.delay(txn_id, pg_txn_id, priority=2)
                
                return {
                    'status': 'queued',
                    'message': 'Transaction not found, queued for refund sync',
                    'txn_id': txn_id
                }
                
        except Exception as e:
            logger.error(f"Error processing refund status webhook: {str(e)}")
            return {'error': f'Refund status processing failed: {str(e)}'}
    
    def _process_settlement_status(self, data: Dict[str, Any], txn_id: str, pg_txn_id: str) -> Dict[str, Any]:
        """Process settlement status webhook"""
        try:
            if not txn_id:
                return {'error': 'Transaction ID missing in webhook'}
            
            # Update transaction settlement details
            try:
                transaction = TransactionDetail.objects.get(txn_id=txn_id)
                
                # Update settlement fields
                if 'settlement_status' in data:
                    transaction.settlement_status = data['settlement_status']
                if 'is_settled' in data:
                    transaction.is_settled = data['is_settled']
                if 'settlement_date' in data:
                    transaction.settlement_date = timezone.datetime.fromisoformat(data['settlement_date'])
                
                transaction.save()
                
                return {
                    'status': 'success',
                    'message': 'Settlement status updated',
                    'txn_id': txn_id,
                    'is_settled': transaction.is_settled
                }
                
            except TransactionDetail.DoesNotExist:
                logger.warning(f"Transaction {txn_id} not found for settlement webhook")
                
                return {
                    'status': 'not_found',
                    'message': 'Transaction not found',
                    'txn_id': txn_id
                }
                
        except Exception as e:
            logger.error(f"Error processing settlement webhook: {str(e)}")
            return {'error': f'Settlement status processing failed: {str(e)}'}


@csrf_exempt
@require_POST
def generic_webhook_handler(request, gateway_code):
    """Generic webhook handler that delegates to the main webhook view"""
    view = GatewayWebhookView()
    return view.post(request, gateway_code)


@csrf_exempt
@require_POST
def webhook_health_check(request):
    """Health check endpoint for webhook system"""
    return JsonResponse({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'message': 'Webhook system is operational'
    })