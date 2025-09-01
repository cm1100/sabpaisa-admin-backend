"""
WebSocket consumers for real-time dashboard updates
Following Django Channels best practices
"""
import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from datetime import timedelta
import random
import logging

logger = logging.getLogger(__name__)


class DashboardConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time dashboard updates
    """
    
    async def connect(self):
        """Accept WebSocket connection"""
        self.room_name = 'dashboard'
        self.room_group_name = f'dashboard_{self.room_name}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Start sending periodic updates
        self.update_task = asyncio.create_task(self.send_periodic_updates())
        
        logger.info(f"WebSocket connected: {self.channel_name}")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Cancel periodic updates
        if hasattr(self, 'update_task'):
            self.update_task.cancel()
        
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        logger.info(f"WebSocket disconnected: {self.channel_name}")
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': timezone.now().isoformat()
                }))
            
            elif message_type == 'subscribe':
                # Handle subscription to specific data streams
                stream = data.get('stream')
                await self.handle_subscription(stream)
            
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
        except Exception as e:
            logger.error(f"Error in receive: {str(e)}")
    
    async def handle_subscription(self, stream):
        """Handle subscription to specific data streams"""
        if stream == 'transactions':
            await self.send_transaction_updates()
        elif stream == 'metrics':
            await self.send_metrics_update()
        elif stream == 'system_health':
            await self.send_system_health()
    
    async def send_periodic_updates(self):
        """Send periodic updates to connected clients"""
        while True:
            try:
                await asyncio.sleep(5)  # Update every 5 seconds
                
                # Send different types of updates
                await self.send_metrics_update()
                await asyncio.sleep(2)
                await self.send_transaction_updates()
                await asyncio.sleep(2)
                await self.send_system_health()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic updates: {str(e)}")
    
    async def send_metrics_update(self):
        """Send dashboard metrics update"""
        metrics = await self.get_dashboard_metrics()
        await self.send(text_data=json.dumps({
            'type': 'metrics_update',
            'data': metrics,
            'timestamp': timezone.now().isoformat()
        }))
    
    async def send_transaction_updates(self):
        """Send recent transaction updates"""
        transactions = await self.get_recent_transactions()
        await self.send(text_data=json.dumps({
            'type': 'transaction_update',
            'data': transactions,
            'timestamp': timezone.now().isoformat()
        }))
    
    async def send_system_health(self):
        """Send system health status"""
        health = await self.get_system_health()
        await self.send(text_data=json.dumps({
            'type': 'system_health',
            'data': health,
            'timestamp': timezone.now().isoformat()
        }))
    
    @database_sync_to_async
    def get_dashboard_metrics(self):
        """Get dashboard metrics from database"""
        # For demo, return mock data
        # In production, fetch from actual services
        return {
            'total_transactions': random.randint(1450000, 1550000),
            'success_rate': round(random.uniform(94, 99), 2),
            'total_volume': round(random.uniform(450000000, 550000000), 2),
            'active_clients': random.randint(2600, 2800),
            'pending_settlements': random.randint(10, 50),
            'tps': random.randint(15, 25)
        }
    
    @database_sync_to_async
    def get_recent_transactions(self):
        """Get recent transactions"""
        # For demo, return mock data
        transactions = []
        for i in range(5):
            transactions.append({
                'txn_id': f"TXN{random.randint(100000, 999999)}",
                'amount': round(random.uniform(100, 10000), 2),
                'status': random.choice(['SUCCESS', 'PENDING', 'FAILED']),
                'client': f"CLIENT{random.randint(100, 999)}",
                'timestamp': (timezone.now() - timedelta(minutes=i)).isoformat()
            })
        return transactions
    
    @database_sync_to_async
    def get_system_health(self):
        """Get system health status"""
        return {
            'api_status': 'healthy',
            'database_status': 'healthy',
            'cache_status': 'healthy',
            'gateway_status': random.choice(['healthy', 'degraded']),
            'cpu_usage': random.randint(20, 60),
            'memory_usage': random.randint(30, 70),
            'response_time': random.randint(50, 200)
        }
    
    # Handler for group messages
    async def dashboard_update(self, event):
        """Handle dashboard update messages from group"""
        await self.send(text_data=json.dumps({
            'type': event['update_type'],
            'data': event['data'],
            'timestamp': event['timestamp']
        }))


class TransactionConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time transaction monitoring
    """
    
    async def connect(self):
        """Accept WebSocket connection"""
        self.room_name = 'transactions'
        self.room_group_name = f'transactions_{self.room_name}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Start transaction stream
        self.stream_task = asyncio.create_task(self.stream_transactions())
        
        logger.info(f"Transaction WebSocket connected: {self.channel_name}")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Cancel streaming task
        if hasattr(self, 'stream_task'):
            self.stream_task.cancel()
        
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        logger.info(f"Transaction WebSocket disconnected: {self.channel_name}")
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'filter':
                # Apply filters to transaction stream
                self.filters = data.get('filters', {})
                await self.send(text_data=json.dumps({
                    'type': 'filter_applied',
                    'filters': self.filters
                }))
            
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
    
    async def stream_transactions(self):
        """Stream transactions in real-time"""
        while True:
            try:
                await asyncio.sleep(2)  # Send update every 2 seconds
                
                # Generate mock transaction
                transaction = {
                    'txn_id': f"TXN{random.randint(100000, 999999)}",
                    'amount': round(random.uniform(100, 50000), 2),
                    'status': random.choice(['SUCCESS', 'SUCCESS', 'SUCCESS', 'PENDING', 'FAILED']),
                    'payment_mode': random.choice(['UPI', 'CARD', 'NET_BANKING', 'WALLET']),
                    'client_code': f"CLIENT{random.randint(100, 999)}",
                    'timestamp': timezone.now().isoformat()
                }
                
                await self.send(text_data=json.dumps({
                    'type': 'new_transaction',
                    'data': transaction
                }))
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in transaction stream: {str(e)}")
    
    # Handler for group messages
    async def transaction_broadcast(self, event):
        """Handle transaction broadcast messages from group"""
        await self.send(text_data=json.dumps({
            'type': 'transaction_update',
            'data': event['transaction'],
            'timestamp': event['timestamp']
        }))