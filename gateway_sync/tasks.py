from celery import shared_task
from django.utils import timezone
from django.db import models
from datetime import timedelta
import requests
import logging
from typing import Dict, Any, Optional
import time

from .models import GatewaySyncQueue, GatewayConfiguration, GatewaySyncLog, TransactionDetail

logger = logging.getLogger('apps')


@shared_task(bind=True, max_retries=3)
def process_sync_queue(self):
    """Process pending items in the gateway sync queue"""
    try:
        start_time = time.time()
        processed_count = 0
        
        # Get items that need processing (PENDING or ready for retry)
        now = timezone.now()
        pending_items = GatewaySyncQueue.objects.filter(
            status__in=['PENDING', 'FAILED'],
            attempts__lt=models.F('max_attempts')
        ).filter(
            models.Q(next_retry_at__isnull=True) | models.Q(next_retry_at__lte=now)
        ).order_by('priority', 'created_at')[:10]  # Process max 10 items per batch
        
        for item in pending_items:
            try:
                # Mark as processing
                item.status = 'PROCESSING'
                item.attempts += 1
                item.save()
                
                # Process based on sync type
                if item.sync_type == 'STATUS_CHECK':
                    result = perform_status_check.delay(item.sync_id)
                elif item.sync_type == 'REFUND_STATUS':
                    result = perform_refund_status_check.delay(item.sync_id)
                elif item.sync_type == 'SETTLEMENT_STATUS':
                    result = perform_settlement_status_check.delay(item.sync_id)
                
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing sync item {item.sync_id}: {str(e)}")
                item.status = 'FAILED'
                item.error_message = str(e)
                item.next_retry_at = now + timedelta(seconds=item.attempts * 30)
                item.save()
        
        processing_time = (time.time() - start_time) * 1000
        logger.info(f"Processed {processed_count} sync items in {processing_time:.2f}ms")
        
        return {
            'processed_count': processed_count,
            'processing_time_ms': processing_time,
            'timestamp': now.isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Error in process_sync_queue: {str(exc)}")
        raise self.retry(exc=exc, countdown=60, max_retries=3)


@shared_task(bind=True, max_retries=3)
def check_pending_transactions(self):
    """Check for pending transactions that need status updates"""
    try:
        start_time = time.time()
        
        # Find pending transactions older than 5 minutes
        cutoff_time = timezone.now() - timedelta(minutes=5)
        pending_transactions = TransactionDetail.objects.filter(
            status='PENDING',
            created_date__lt=cutoff_time
        )[:50]  # Limit to 50 per run
        
        queued_count = 0
        for txn in pending_transactions:
            # Check if already queued for status check
            existing_queue = GatewaySyncQueue.objects.filter(
                txn_id=txn.txn_id,
                sync_type='STATUS_CHECK',
                status__in=['PENDING', 'PROCESSING']
            ).exists()
            
            if not existing_queue:
                # Create queue entry for status check
                GatewaySyncQueue.objects.create(
                    txn_id=txn.txn_id,
                    pg_txn_id=txn.pg_txn_id,
                    sync_type='STATUS_CHECK',
                    priority=1,  # High priority for pending transactions
                    request_data={'check_type': 'pending_status_check'}
                )
                queued_count += 1
        
        processing_time = (time.time() - start_time) * 1000
        logger.info(f"Queued {queued_count} pending transactions for status check in {processing_time:.2f}ms")
        
        return {
            'queued_count': queued_count,
            'processing_time_ms': processing_time,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Error in check_pending_transactions: {str(exc)}")
        raise self.retry(exc=exc, countdown=30, max_retries=3)


@shared_task(bind=True, max_retries=3)
def retry_failed_syncs(self):
    """Retry failed sync operations with exponential backoff"""
    try:
        start_time = time.time()
        now = timezone.now()
        
        # Find failed items ready for retry
        failed_items = GatewaySyncQueue.objects.filter(
            status='FAILED',
            attempts__lt=models.F('max_attempts'),
            next_retry_at__lte=now
        ).order_by('priority', 'next_retry_at')[:20]  # Process max 20 retries per run
        
        retry_count = 0
        for item in failed_items:
            # Reset to pending for retry
            item.status = 'PENDING'
            item.next_retry_at = None
            item.save()
            retry_count += 1
        
        processing_time = (time.time() - start_time) * 1000
        logger.info(f"Reset {retry_count} failed items for retry in {processing_time:.2f}ms")
        
        return {
            'retry_count': retry_count,
            'processing_time_ms': processing_time,
            'timestamp': now.isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Error in retry_failed_syncs: {str(exc)}")
        raise self.retry(exc=exc, countdown=60, max_retries=3)


@shared_task(bind=True, max_retries=3)
def perform_status_check(self, sync_id: int):
    """Perform actual status check with gateway"""
    sync_item = None
    try:
        start_time = time.time()
        sync_item = GatewaySyncQueue.objects.get(sync_id=sync_id)
        
        # Get gateway configuration
        transaction = TransactionDetail.objects.get(txn_id=sync_item.txn_id)
        gateway_config = GatewayConfiguration.objects.get(
            gateway_code=transaction.pg_name,
            is_active=True
        )
        
        # Prepare request
        headers = {
            'Authorization': f'Bearer {gateway_config.api_key}',
            'Content-Type': 'application/json'
        }
        
        request_data = {
            'txn_id': sync_item.txn_id,
            'pg_txn_id': sync_item.pg_txn_id
        }
        
        # Log the request
        log_entry = GatewaySyncLog.objects.create(
            sync_queue_id=sync_id,
            operation='STATUS_CHECK',
            request_url=gateway_config.status_check_endpoint,
            request_method='POST',
            request_headers=headers,
            request_body=request_data
        )
        
        # Make API call
        response = requests.post(
            gateway_config.status_check_endpoint,
            json=request_data,
            headers=headers,
            timeout=gateway_config.timeout_seconds
        )
        
        response_time = (time.time() - start_time) * 1000
        
        # Update log with response
        log_entry.response_status = response.status_code
        log_entry.response_headers = dict(response.headers)
        log_entry.response_body = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
        log_entry.response_time_ms = int(response_time)
        log_entry.success = response.status_code == 200
        log_entry.save()
        
        # Update sync queue item
        sync_item.response_data = log_entry.response_body
        sync_item.processed_at = timezone.now()
        
        if response.status_code == 200:
            # Update transaction status if needed
            response_data = response.json()
            if 'status' in response_data:
                transaction.status = response_data['status']
                transaction.save()
            
            sync_item.status = 'COMPLETED'
            logger.info(f"Status check completed for {sync_item.txn_id} in {response_time:.2f}ms")
        else:
            sync_item.status = 'FAILED'
            sync_item.error_message = f"HTTP {response.status_code}: {response.text}"
            
        sync_item.save()
        
        return {
            'sync_id': sync_id,
            'status': sync_item.status,
            'response_time_ms': response_time,
            'timestamp': timezone.now().isoformat()
        }
        
    except GatewayConfiguration.DoesNotExist:
        error_msg = f"Gateway configuration not found for transaction {sync_item.txn_id if sync_item else 'unknown'}"
        logger.error(error_msg)
        if sync_item:
            sync_item.status = 'FAILED'
            sync_item.error_message = error_msg
            sync_item.save()
        return {'error': error_msg}
        
    except Exception as exc:
        error_msg = f"Error in perform_status_check: {str(exc)}"
        logger.error(error_msg)
        if sync_item:
            sync_item.status = 'FAILED'
            sync_item.error_message = error_msg
            sync_item.next_retry_at = timezone.now() + timedelta(seconds=sync_item.attempts * 30)
            sync_item.save()
        raise self.retry(exc=exc, countdown=30, max_retries=3)


@shared_task(bind=True, max_retries=3)
def perform_refund_status_check(self, sync_id: int):
    """Check refund status with gateway"""
    sync_item = None
    try:
        start_time = time.time()
        sync_item = GatewaySyncQueue.objects.get(sync_id=sync_id)
        
        # Get gateway configuration
        transaction = TransactionDetail.objects.get(txn_id=sync_item.txn_id)
        gateway_config = GatewayConfiguration.objects.get(
            gateway_code=transaction.pg_name,
            is_active=True
        )
        
        if not gateway_config.refund_endpoint:
            error_msg = f"No refund endpoint configured for gateway {gateway_config.gateway_code}"
            sync_item.status = 'FAILED'
            sync_item.error_message = error_msg
            sync_item.save()
            return {'error': error_msg}
        
        # Prepare request
        headers = {
            'Authorization': f'Bearer {gateway_config.api_key}',
            'Content-Type': 'application/json'
        }
        
        request_data = {
            'txn_id': sync_item.txn_id,
            'pg_txn_id': sync_item.pg_txn_id,
            'operation': 'refund_status'
        }
        
        # Log the request
        log_entry = GatewaySyncLog.objects.create(
            sync_queue_id=sync_id,
            operation='REFUND_STATUS',
            request_url=gateway_config.refund_endpoint,
            request_method='POST',
            request_headers=headers,
            request_body=request_data
        )
        
        # Make API call
        response = requests.post(
            gateway_config.refund_endpoint,
            json=request_data,
            headers=headers,
            timeout=gateway_config.timeout_seconds
        )
        
        response_time = (time.time() - start_time) * 1000
        
        # Update log with response
        log_entry.response_status = response.status_code
        log_entry.response_headers = dict(response.headers)
        log_entry.response_body = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
        log_entry.response_time_ms = int(response_time)
        log_entry.success = response.status_code == 200
        log_entry.save()
        
        # Update sync queue and transaction
        sync_item.response_data = log_entry.response_body
        sync_item.processed_at = timezone.now()
        
        if response.status_code == 200:
            response_data = response.json()
            
            # Update transaction refund details
            if 'refund_status' in response_data:
                transaction.refund_status_code = response_data.get('refund_status')
                transaction.is_refunded = response_data.get('is_refunded', False)
                transaction.refunded_amount = response_data.get('refunded_amount')
                transaction.refund_message = response_data.get('refund_message')
                if transaction.is_refunded and 'refunded_date' in response_data:
                    transaction.refunded_date = timezone.datetime.fromisoformat(response_data['refunded_date'])
                transaction.save()
            
            sync_item.status = 'COMPLETED'
            logger.info(f"Refund status check completed for {sync_item.txn_id} in {response_time:.2f}ms")
        else:
            sync_item.status = 'FAILED'
            sync_item.error_message = f"HTTP {response.status_code}: {response.text}"
        
        sync_item.save()
        
        return {
            'sync_id': sync_id,
            'status': sync_item.status,
            'response_time_ms': response_time,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as exc:
        error_msg = f"Error in perform_refund_status_check: {str(exc)}"
        logger.error(error_msg)
        if sync_item:
            sync_item.status = 'FAILED'
            sync_item.error_message = error_msg
            sync_item.next_retry_at = timezone.now() + timedelta(seconds=sync_item.attempts * 30)
            sync_item.save()
        raise self.retry(exc=exc, countdown=30, max_retries=3)


@shared_task(bind=True, max_retries=3)
def perform_settlement_status_check(self, sync_id: int):
    """Check settlement status with gateway"""
    sync_item = None
    try:
        start_time = time.time()
        sync_item = GatewaySyncQueue.objects.get(sync_id=sync_id)
        
        # Get gateway configuration
        transaction = TransactionDetail.objects.get(txn_id=sync_item.txn_id)
        gateway_config = GatewayConfiguration.objects.get(
            gateway_code=transaction.pg_name,
            is_active=True
        )
        
        # Prepare request
        headers = {
            'Authorization': f'Bearer {gateway_config.api_key}',
            'Content-Type': 'application/json'
        }
        
        request_data = {
            'txn_id': sync_item.txn_id,
            'pg_txn_id': sync_item.pg_txn_id,
            'operation': 'settlement_status'
        }
        
        # Log the request
        log_entry = GatewaySyncLog.objects.create(
            sync_queue_id=sync_id,
            operation='SETTLEMENT_STATUS',
            request_url=gateway_config.api_endpoint,  # Use main endpoint for settlement checks
            request_method='POST',
            request_headers=headers,
            request_body=request_data
        )
        
        # Make API call
        response = requests.post(
            gateway_config.api_endpoint,
            json=request_data,
            headers=headers,
            timeout=gateway_config.timeout_seconds
        )
        
        response_time = (time.time() - start_time) * 1000
        
        # Update log with response
        log_entry.response_status = response.status_code
        log_entry.response_headers = dict(response.headers)
        log_entry.response_body = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
        log_entry.response_time_ms = int(response_time)
        log_entry.success = response.status_code == 200
        log_entry.save()
        
        # Update sync queue and transaction
        sync_item.response_data = log_entry.response_body
        sync_item.processed_at = timezone.now()
        
        if response.status_code == 200:
            response_data = response.json()
            
            # Update transaction settlement details
            if 'settlement_status' in response_data:
                transaction.settlement_status = response_data.get('settlement_status')
                transaction.is_settled = response_data.get('is_settled', False)
                if transaction.is_settled and 'settlement_date' in response_data:
                    transaction.settlement_date = timezone.datetime.fromisoformat(response_data['settlement_date'])
                transaction.save()
            
            sync_item.status = 'COMPLETED'
            logger.info(f"Settlement status check completed for {sync_item.txn_id} in {response_time:.2f}ms")
        else:
            sync_item.status = 'FAILED'
            sync_item.error_message = f"HTTP {response.status_code}: {response.text}"
        
        sync_item.save()
        
        return {
            'sync_id': sync_id,
            'status': sync_item.status,
            'response_time_ms': response_time,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as exc:
        error_msg = f"Error in perform_settlement_status_check: {str(exc)}"
        logger.error(error_msg)
        if sync_item:
            sync_item.status = 'FAILED'
            sync_item.error_message = error_msg
            sync_item.next_retry_at = timezone.now() + timedelta(seconds=sync_item.attempts * 30)
            sync_item.save()
        raise self.retry(exc=exc, countdown=30, max_retries=3)


@shared_task(bind=True)
def queue_status_check(self, txn_id: str, pg_txn_id: str = None, priority: int = 2):
    """Queue a status check for a specific transaction"""
    try:
        # Check if already queued
        existing_queue = GatewaySyncQueue.objects.filter(
            txn_id=txn_id,
            sync_type='STATUS_CHECK',
            status__in=['PENDING', 'PROCESSING']
        ).exists()
        
        if not existing_queue:
            sync_item = GatewaySyncQueue.objects.create(
                txn_id=txn_id,
                pg_txn_id=pg_txn_id,
                sync_type='STATUS_CHECK',
                priority=priority,
                request_data={'queued_by': 'manual_api_call'}
            )
            
            logger.info(f"Queued status check for transaction {txn_id}")
            return {
                'sync_id': sync_item.sync_id,
                'queued': True,
                'timestamp': timezone.now().isoformat()
            }
        else:
            return {
                'queued': False,
                'message': 'Status check already queued',
                'timestamp': timezone.now().isoformat()
            }
            
    except Exception as exc:
        logger.error(f"Error queuing status check for {txn_id}: {str(exc)}")
        raise exc


@shared_task(bind=True)
def queue_refund_status_check(self, txn_id: str, pg_txn_id: str = None, priority: int = 1):
    """Queue a refund status check for a specific transaction"""
    try:
        # Check if already queued
        existing_queue = GatewaySyncQueue.objects.filter(
            txn_id=txn_id,
            sync_type='REFUND_STATUS',
            status__in=['PENDING', 'PROCESSING']
        ).exists()
        
        if not existing_queue:
            sync_item = GatewaySyncQueue.objects.create(
                txn_id=txn_id,
                pg_txn_id=pg_txn_id,
                sync_type='REFUND_STATUS',
                priority=priority,
                request_data={'queued_by': 'manual_api_call'}
            )
            
            logger.info(f"Queued refund status check for transaction {txn_id}")
            return {
                'sync_id': sync_item.sync_id,
                'queued': True,
                'timestamp': timezone.now().isoformat()
            }
        else:
            return {
                'queued': False,
                'message': 'Refund status check already queued',
                'timestamp': timezone.now().isoformat()
            }
            
    except Exception as exc:
        logger.error(f"Error queuing refund status check for {txn_id}: {str(exc)}")
        raise exc


@shared_task(bind=True)
def sync_transaction_status(self, txn_id: str, force: bool = False):
    """Sync a single transaction status immediately"""
    try:
        start_time = time.time()
        
        # Check if sync is already in progress
        if not force:
            in_progress = GatewaySyncQueue.objects.filter(
                txn_id=txn_id,
                status='PROCESSING'
            ).exists()
            
            if in_progress:
                return {
                    'sync_started': False,
                    'message': 'Sync already in progress',
                    'timestamp': timezone.now().isoformat()
                }
        
        # Create high priority sync item
        sync_item = GatewaySyncQueue.objects.create(
            txn_id=txn_id,
            sync_type='STATUS_CHECK',
            priority=1,  # High priority
            request_data={'immediate_sync': True, 'force': force}
        )
        
        # Trigger immediate processing
        result = perform_status_check.delay(sync_item.sync_id)
        
        processing_time = (time.time() - start_time) * 1000
        logger.info(f"Immediate sync queued for {txn_id} in {processing_time:.2f}ms")
        
        return {
            'sync_id': sync_item.sync_id,
            'sync_started': True,
            'task_id': result.id,
            'processing_time_ms': processing_time,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Error in sync_transaction_status for {txn_id}: {str(exc)}")
        raise exc